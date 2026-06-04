#!/usr/bin/env python3
"""
Per-account self-calibration from the outcomes log (Tier 3 — no cross-account pooling).

Reads clients/{Client}/outcomes-log.csv (closed rows) and produces, per lever:
  - prior levers → strength multiplier = median(actual_rev_delta / predicted_rev)
                   (nudge that lever's hypothesized edge for THIS account next run)
  - exact levers → attainment factor   = median(actual_rev_delta / predicted_rev)
                   (what fraction of the theoretical benchmark-gap this account captures)

Usage:
  python3 calibrate.py --log clients/Acme-Co/outcomes-log.csv [--out calibration.json]
"""
import csv, json, argparse, statistics, collections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    ratios = collections.defaultdict(lambda: {"method": None, "vals": []})
    closed = 0
    for r in csv.DictReader(open(a.log)):
        if (r.get("status", "").strip() != "closed"):
            continue
        try:
            pred = float(r["predicted_rev"]); act = float(r["actual_rev_delta"])
        except (TypeError, ValueError, KeyError):
            continue
        if pred == 0:
            continue
        closed += 1
        lev = r["lever"].strip()
        ratios[lev]["method"] = r.get("method", "").strip()
        ratios[lev]["vals"].append(act / pred)

    out = {}
    for lev, d in ratios.items():
        if not d["vals"]:
            continue
        m = round(statistics.median(d["vals"]), 3)
        kind = "attainment_factor" if d["method"] == "exact" else "strength_multiplier"
        out[lev] = {"method": d["method"], kind: m, "n": len(d["vals"])}

    print(f"CALIBRATION — {closed} closed outcomes across {len(out)} levers\n")
    if not out:
        print("  No closed outcomes yet. Log predictions now; revisit at 30/60/90 days.")
    for lev, d in sorted(out.items(), key=lambda kv: kv[1].get("n", 0), reverse=True):
        k = "attainment_factor" if d["method"] == "exact" else "strength_multiplier"
        tip = ("realistic = exact × " + str(d[k])) if d["method"] == "exact" else ("nudge edge × " + str(d[k]))
        print(f"  {lev:<16} {d['method']:<6} {k}={d[k]:<6} (n={d['n']})  → {tip}")
    print("\nApply these per-account next run. Never pool across accounts.")

    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
