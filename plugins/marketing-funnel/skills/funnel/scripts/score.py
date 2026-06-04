#!/usr/bin/env python3
"""
Funnel Prioritizer scoring engine (v3 — exact where it's math, prior where it isn't).

Two ways a lever's revenue impact is computed:
  EXACT  — for identity / conversion-rate / AOV factor levers, the impact of moving
           current→target is arithmetic from THIS account's own numbers:
             Δrev = base × (p_target / p_current − 1)
           (p = the value, or 1−value for negative drivers; base = revenue, or
            ret_baseline for retention factors). No edge strength involved.
  PRIOR  — for lagged / statistical levers (TOF volume, capture, halo), use the
           hypothesized graph sensitivity: rev = baseline × elasticity × headroom.

Each lever is labelled 'exact' or 'prior' so the report shows which numbers are math
and which are still estimates. No cross-account pooling is required.

Usage:
  python3 score.py --values FILE --baseline 850000 --cm2 35 [--ret-baseline 300000] [--k 0.13] --out levers.json
"""
import csv, os, json, math, argparse, heapq

HERE = os.path.dirname(os.path.abspath(__file__))
REF  = os.path.join(HERE, "..", "references")
OUTPUTS = {"revenue", "orders", "sessions", "cvr_id", "ret_rev", "aov", "cvr"}
PAID = {"tof_spend", "impressions", "reach", "frequency", "cpm", "cpc"}
# multiplicative factors of site revenue (moving them is exact, ceteris paribus)
EXACT_REV = {"pdp_rate", "atc_rate", "ic_rate", "checkout", "cart_aband", "co_aband", "upo", "asp"}
# multiplicative factors of returning revenue (exact when --ret-baseline is supplied)
EXACT_RET = {"repeat_rate", "freq", "ltv"}


def load_graph():
    nodes = {}
    for r in csv.reader(open(os.path.join(REF, "funnel-nodes.csv"))):
        if r and r[0] != "id":
            nodes[r[0]] = {"label": r[1], "layer": r[2]}
    out = {k: [] for k in nodes}
    for r in csv.reader(open(os.path.join(REF, "funnel-edges.csv"))):
        if r and r[0] != "source":
            out[r[0]].append({"t": r[1], "w": float(r[2]),
                              "sign": -1.0 if r[3] == "negative" else 1.0,
                              "lag": float(r[4]), "type": r[5]})
    return nodes, out


def sensitivity(nodes, out):
    I = {k: 0.0 for k in nodes}; I["revenue"] = 1.0
    for _ in range(500):
        nI = {k: 0.0 for k in nodes}; nI["revenue"] = 1.0
        for n in nodes:
            if n != "revenue":
                nI[n] = sum(e["w"] * e["sign"] * I[e["t"]] for e in out[n])
        if max(abs(nI[k] - I[k]) for k in nodes) < 1e-9:
            return nI
        I = nI
    return I


def chain(start, out, nodes):
    if start == "revenue":
        return []
    dist = {start: 0.0}; prev = {}; pq = [(0.0, start)]
    while pq:
        d, x = heapq.heappop(pq)
        if x == "revenue":
            break
        if d > dist.get(x, 1e18):
            continue
        for e in out.get(x, []):
            w = abs(e["w"])
            if w > 0:
                nd = d - math.log(w)
                if nd < dist.get(e["t"], 1e18):
                    dist[e["t"]] = nd; prev[e["t"]] = (x, e); heapq.heappush(pq, (nd, e["t"]))
    if "revenue" not in prev:
        return []
    ch = []; cur = "revenue"
    while cur in prev:
        p, e = prev[cur]
        ch.append({"from": p, "from_label": nodes[p]["label"], "to": cur, "to_label": nodes[cur]["label"],
                   "strength": round(e["w"], 2), "sign": int(e["sign"]), "lag": e["lag"], "type": e["type"]})
        cur = p
    ch.reverse(); return ch


def hr(c, b, hib):
    try:
        c, b = float(c), float(b)
    except (TypeError, ValueError):
        return 0.0
    v = (b - c) / b if (hib and b) else ((c - b) / c if (not hib and c) else 0.0)
    return max(0.0, min(1.0, round(v, 3)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--values", default=os.path.join(REF, "sample-node-values.csv"))
    ap.add_argument("--baseline", type=float, default=850000.0)
    ap.add_argument("--ret-baseline", type=float, default=0.0, dest="ret_baseline",
                    help="returning-revenue $/mo; enables EXACT for retention factors")
    ap.add_argument("--cm2", default="35")
    ap.add_argument("--k", type=float, default=0.13)
    ap.add_argument("--attainment", type=float, default=0.35,
                    help="default fraction of an EXACT ceiling an account realistically captures, "
                         "until the outcomes log calibrates a per-lever attainment factor")
    ap.add_argument("--score-anchor", type=float, default=0.8, dest="score_anchor",
                    help="FIXED anchor for the 0-100 opportunity score: opp = 100 × headroom × |sensitivity| / anchor, "
                         "capped at 100. 0.8 ≈ a high-leverage lever (sensitivity ~1.2) with half its benchmark gap "
                         "still open scores ~75/100. Lower anchor = more generous scores. Kept FIXED (not normalized "
                         "to the top lever of one run) so a 78 means the same thing across runs and across clients.")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cm2 = float(a.cm2); cm2 = cm2 / 100 if cm2 > 1 else cm2

    nodes, out = load_graph()
    I = sensitivity(nodes, out)
    vals = {r["id"].strip(): r for r in csv.DictReader(open(a.values)) if r.get("id")}
    mappable = [n for n in nodes if n not in OUTPUTS]

    rows = []
    for nid, v in vals.items():
        if nid not in nodes or nid in OUTPUTS:
            continue
        if str(v.get("measured", "1")).strip() not in ("1", "true", "True"):
            continue
        hib = str(v.get("higher_is_better", "1")).strip() in ("1", "true", "True")
        try:
            cur_f, tgt_f = float(v.get("current")), float(v.get("benchmark"))
        except (TypeError, ValueError):
            cur_f = tgt_f = None
        h = hr(v.get("current"), v.get("benchmark"), hib)
        sens = abs(I.get(nid, 0.0)); elasticity = round(sens * a.k, 4)

        method = "prior"; base = "rev"; rev = round(a.baseline * elasticity * h)
        if cur_f and tgt_f and nid in EXACT_REV:
            pc, pt = (cur_f, tgt_f) if hib else (1 - cur_f, 1 - tgt_f)
            if pc > 0:
                rev = max(0, round(a.baseline * (pt / pc - 1))); method = "exact"; base = "rev"
        elif cur_f and tgt_f and nid in EXACT_RET and a.ret_baseline > 0 and cur_f > 0:
            rev = max(0, round(a.ret_baseline * (tgt_f / cur_f - 1))); method = "exact"; base = "ret"

        incr = (v.get("incr_spend") or "").strip()
        if incr:
            prof = round(rev * cm2 - float(incr)); pnote = "measured"
        elif nid in PAID:
            prof = None; pnote = "needs spend input"
        else:
            prof = round(rev * cm2); pnote = "measured"
        att = a.attainment if method == "exact" else 1.0
        rev_real = round(rev * att)
        prof_real = (None if prof is None else round(prof * att))
        # 0-100 opportunity score = headroom × sensitivity on a FIXED anchor (see --score-anchor).
        # Same Headroom × Sensitivity that drives the dollars, expressed as a comparable, low-false-precision unit.
        opp_raw = round(h * sens, 4)
        opportunity = round(min(100.0, 100.0 * opp_raw / a.score_anchor)) if a.score_anchor > 0 else 0

        rows.append({
            "id": nid, "label": nodes[nid]["label"], "layer": nodes[nid]["layer"],
            "direction": "increase" if I.get(nid, 0.0) >= 0 else "reduce",
            "current": v.get("current"), "benchmark": v.get("benchmark"),
            "current_f": cur_f, "target_f": tgt_f, "higher_is_better": 1 if hib else 0,
            "method": method, "base": base, "source": v.get("source", ""), "window": v.get("window", ""),
            "sensitivity": round(sens, 3), "elasticity": elasticity, "headroom": h,
            "opportunity": opportunity, "opp_raw": opp_raw,
            "attainment": round(att, 3),
            "revenue_usd": rev, "profit_usd": prof, "profit_note": pnote,
            "revenue_real": rev_real, "profit_real": prof_real,
            "cost_class": "paid" if nid in PAID else "margin",
            "confidence": ("UNVERIFIED" if not v.get("source") else method),
            "chain": chain(nid, out, nodes),
        })

    coverage = len(rows) / len(mappable) if mappable else 0
    rev_rank = sorted(rows, key=lambda r: -r["revenue_real"])
    prof_rank = sorted([r for r in rows if r["profit_real"] is not None], key=lambda r: -r["profit_real"])

    def fmt(n): return "—" if n is None else f"${n:,.0f}"
    print(f"\nFUNNEL PRIORITIZER v3 — baseline {fmt(a.baseline)}/mo"
          + (f" (ret {fmt(a.ret_baseline)})" if a.ret_baseline else "")
          + f" · CM2 {cm2:.0%} · attainment {a.attainment:.0%} · measured {len(rows)}/{len(mappable)} ({coverage:.0%})\n")
    if rev_rank:
        r = rev_rank[0]; print(f"BIGGEST REVENUE LEVER → {r['label']} ({r['direction']}, {r['method']}) "
                               f"~{fmt(r['revenue_real'])}/mo realistic" + (f" (ceiling {fmt(r['revenue_usd'])})" if r['method']=='exact' else ""))
    if prof_rank:
        r = prof_rank[0]; print(f"BIGGEST PROFIT  LEVER → {r['label']} ({r['direction']}, {r['method']}) ~{fmt(r['profit_real'])}/mo realistic")
    print("\n#  opp/100  now→target            realistic  conf   lever")
    for i, r in enumerate(rev_rank[:a.top], 1):
        gap = f"{r['current']}→{r['benchmark']}"
        print(f"{i}   {r['opportunity']:>3}    {gap:<18}  {fmt(r['revenue_real']):>9}  {r['method']:<5}  {r['label']}")
    print("\nEXACT ceiling = identity arithmetic (ceteris paribus, full benchmark attainment). Realistic = ceiling × attainment.")
    print("PRIOR = hypothesized strength; self-calibrates per account via the outcomes log.")

    if a.out:
        measured_ids = {r["id"] for r in rows}
        gaps = sorted(((n, abs(I.get(n, 0.0))) for n in mappable if n not in measured_ids),
                      key=lambda x: -x[1])[:6]
        data_gaps = [{"label": nodes[n]["label"], "layer": nodes[n]["layer"], "sensitivity": round(s, 3)}
                     for n, s in gaps]
        json.dump({"meta": {"baseline": a.baseline, "ret_baseline": a.ret_baseline, "cm2": cm2,
                            "k": a.k, "attainment": a.attainment, "score_anchor": a.score_anchor,
                            "coverage": round(coverage, 3),
                            "measured": len(rows), "mappable": len(mappable), "data_gaps": data_gaps},
                   "revenue": rev_rank, "profit": prof_rank}, open(a.out, "w"), indent=2)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
