#!/usr/bin/env python3
"""
Hallucination gate for the Funnel Prioritizer.

Fails (exit 1) the run if ANY of these is true:
  - a scored metric value has no source/window  (invented number)
  - a lever's revenue $ doesn't equal baseline × elasticity × headroom  (invented dollars)
  - a why-chain edge isn't present in the verified graph  (invented causality)
  - a play names a campaign/flow/offer not in the live inventory  (invented entity)
  - a play's target→intermediate isn't a real edge, or intermediate can't reach the outcome
  - an output/identity node is ranked as a pullable lever

No report may be emitted unless this exits 0.

Usage (full run):
  python3 verify.py --values FILE --levers levers.json [--plays plays.json] [--inventory inv.csv]

Usage (values-only / baseline check — no levers yet):
  python3 verify.py --values FILE
  When --levers is omitted, lever/dollar/chain checks are skipped.
  When --plays  is omitted, play checks are skipped.
  When --inventory is omitted, entity-grounding checks are skipped.
  The 88-node coverage check and provenance checks ALWAYS run.
"""
import csv, os, sys, json, argparse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REF  = os.path.join(HERE, "..", "references")
OUTPUTS = {"revenue", "orders", "sessions", "cvr_id", "ret_rev", "aov", "cvr"}


def load_graph():
    nodes = set()
    for r in csv.reader(open(os.path.join(REF, "funnel-nodes.csv"))):
        if r and r[0] != "id":
            nodes.add(r[0])
    adj = collections.defaultdict(list); edgeset = set()
    for r in csv.reader(open(os.path.join(REF, "funnel-edges.csv"))):
        if r and r[0] != "source":
            adj[r[0]].append(r[1]); edgeset.add((r[0], r[1]))
    return nodes, adj, edgeset


def reaches(adj, s, t):
    if s == t:
        return True
    seen = {s}; st = [s]
    while st:
        x = st.pop()
        for y in adj.get(x, []):
            if y == t:
                return True
            if y not in seen:
                seen.add(y); st.append(y)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--values", required=True)
    ap.add_argument("--levers", default=None)
    ap.add_argument("--plays", default=None)
    ap.add_argument("--inventory", default=None)
    a = ap.parse_args()

    nodes, adj, edgeset = load_graph()
    V = []

    # 0. completeness — every node id must have exactly one row in node-values.csv
    from pathlib import Path
    ref_nodes_path = Path(__file__).resolve().parent.parent / "references" / "funnel-nodes.csv"
    ref_ids = []
    for r in csv.DictReader(open(ref_nodes_path)):
        if r.get("id"):
            ref_ids.append(r["id"])
    ref_id_set = set(ref_ids)
    values_ids = []
    for r in csv.DictReader(open(a.values)):
        if r.get("id"):
            values_ids.append(r["id"])
    seen_ids = {}
    dup_ids = []
    for vid in values_ids:
        if vid in seen_ids:
            dup_ids.append(vid)
        seen_ids[vid] = True
    if dup_ids:
        V.append(f"COVERAGE: node-values.csv has duplicate ids: {', '.join(sorted(set(dup_ids)))}")
    missing_ids = sorted(ref_id_set - set(values_ids))
    if missing_ids:
        V.append(
            f"COVERAGE: node-values.csv is missing {len(missing_ids)} of {len(ref_ids)} nodes: "
            f"{', '.join(missing_ids)} — every node needs a row (value, DATA_NOT_AVAILABLE, or "
            f"NOT_PULLABLE per SKILL.md Step 1)"
        )

    # 1. provenance on measured values
    for r in csv.DictReader(open(a.values)):
        if not r.get("id"):
            continue
        if str(r.get("measured", "1")).strip() in ("1", "true", "True"):
            if not (r.get("source", "").strip() and r.get("window", "").strip()):
                V.append(f"PROVENANCE: '{r['id']}' is measured but missing source/window")

    levers = []
    if a.levers is not None:
        data = json.load(open(a.levers)); meta = data.get("meta", {})
        base = meta.get("baseline"); ret_base = meta.get("ret_baseline", 0) or 0
        levers = data.get("revenue", [])

        for L in levers:
            nid = L["id"]
            # 5. no output nodes as levers
            if nid in OUTPUTS:
                V.append(f"LEVER: output/identity node '{nid}' ranked as a lever")
            # 1b. confidence
            if L.get("confidence") == "UNVERIFIED" or not L.get("source"):
                V.append(f"PROVENANCE: lever '{nid}' has no source")
            # 2. dollar recompute — by method (exact arithmetic vs prior elasticity)
            try:
                if L.get("method") == "exact":
                    c, t, hib = float(L["current_f"]), float(L["target_f"]), int(L["higher_is_better"])
                    if L.get("base") == "ret":
                        expect = max(0, round(ret_base * (t / c - 1)))
                    else:
                        pc, pt = (c, t) if hib else (1 - c, 1 - t)
                        expect = max(0, round(base * (pt / pc - 1)))
                else:
                    expect = round(base * float(L["elasticity"]) * float(L["headroom"]))
                if abs(expect - L["revenue_usd"]) > 1:
                    V.append(f"DOLLARS: '{nid}' revenue_usd {L['revenue_usd']} != {L.get('method')} formula {expect}")
                att = meta.get("attainment", 1.0) if L.get("method") == "exact" else 1.0
                if "revenue_real" in L and abs(round(L["revenue_usd"] * att) - L["revenue_real"]) > 1:
                    V.append(f"DOLLARS: '{nid}' revenue_real {L['revenue_real']} != ceiling×attainment {round(L['revenue_usd'] * att)}")
            except Exception as e:
                V.append(f"DOLLARS: '{nid}' could not recompute ({e})")
            # 3. chain edges exist in graph
            for e in L.get("chain", []):
                if (e["from"], e["to"]) not in edgeset:
                    V.append(f"CHAIN: '{nid}' uses non-existent edge {e['from']}→{e['to']}")

    # 4. plays grounding
    if a.plays is not None:
        plays = json.load(open(a.plays))
        inv_names = set()
        if a.inventory:
            for r in csv.DictReader(open(a.inventory)):
                if r.get("name"):
                    inv_names.add(r["name"].strip())
        for p in plays:
            for ent in p.get("referenced_entities", []):
                if a.inventory and ent not in inv_names:
                    V.append(f"ENTITY: play for '{p.get('lever')}' names '{ent}' not in inventory (hallucinated)")
            if p.get("referenced_entities") and not p.get("grounded"):
                V.append(f"GROUNDING: play for '{p.get('lever')}' references entities but grounded=false")
            tm, im, om = p.get("target_metric"), p.get("intermediate_metric"), p.get("outcome_metric")
            for m in (tm, im, om):
                if m not in nodes:
                    V.append(f"WHY: play for '{p.get('lever')}' uses unknown metric '{m}'")
            if tm in nodes and im in nodes and (tm, im) not in edgeset:
                V.append(f"WHY: play for '{p.get('lever')}' claims {tm}→{im} but no such edge exists")
            if im in nodes and om in nodes and not reaches(adj, im, om):
                V.append(f"WHY: play for '{p.get('lever')}' — {im} has no path to {om}")

    if V:
        print(f"VERIFY FAILED — {len(V)} violation(s):")
        for v in V:
            print("  ✗ " + v)
        sys.exit(1)
    if a.levers is not None:
        print(f"VERIFY PASSED — {len(levers)} levers, provenance + dollars + chains + plays all grounded.")
    else:
        print("VERIFY PASSED (values-only) — coverage + provenance checks clean.")
    sys.exit(0)


if __name__ == "__main__":
    main()
