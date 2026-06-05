#!/usr/bin/env python3
"""Inject the live funnel graph into a run's report.html and maintain history.csv.

Usage:
  python3 scripts/build_graph.py \
      --values clients/{C}/funnel/{date}/node-values.csv \
      --period 2026-05-25..2026-05-31 \
      [--baseline-values clients/{C}/funnel/{date}/node-values-baseline.csv \
       --baseline-period 2026-05-18..2026-05-24] \
      --client "{C}" [--pulled-at {date}] \
      --report clients/{C}/funnel/{date}/report.html \
      [--standalone out.html]
"""
import argparse, csv, json, re, sys
from datetime import date as _date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REFS = SKILL_DIR / "references"
HISTORY_FIELDS = ["period_start", "period_end", "grain", "pulled_at",
                  "node_id", "current", "benchmark", "higher_is_better",
                  "measured", "source"]
LAYER_KEY = {"tof": "tof", "mof": "mof", "bof": "bof", "aov": "aov",
             "retention": "ret", "spine": "spine", "revenue": "out"}
START_MARK = "<!-- FUNNEL_GRAPH_START -->"
END_MARK = "<!-- FUNNEL_GRAPH_END -->"


# ---------------------------------------------------------------------------
# Period helpers
# ---------------------------------------------------------------------------

def parse_period(p):
    """Parse 'YYYY-MM-DD..YYYY-MM-DD' -> (start, end). Raises ValueError on bad input."""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$", str(p).strip())
    if not m:
        raise ValueError(f"bad period (want YYYY-MM-DD..YYYY-MM-DD): {p}")
    s, e = m.group(1), m.group(2)
    if e < s:
        raise ValueError(f"period end before start: {p}")
    return s, e


def derive_grain(start, end):
    """Compute grain from dates; never trust the caller's claim."""
    s = _date.fromisoformat(start)
    e = _date.fromisoformat(end)
    return "week" if (s.weekday() == 0 and e.weekday() == 6 and (e - s).days == 6) else "adhoc"


# ---------------------------------------------------------------------------
# node-values.csv reader
# ---------------------------------------------------------------------------

def read_values(path):
    """node-values.csv -> list of value dicts (no period fields yet)."""
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append({"node_id": r["id"].strip(),
                        "current": (r.get("current") or "").strip(),
                        "benchmark": (r.get("benchmark") or "").strip(),
                        "higher_is_better": (r.get("higher_is_better") or "1").strip(),
                        "measured": (r.get("measured") or "0").strip(),
                        "source": (r.get("source") or "").strip()})
    return out


# ---------------------------------------------------------------------------
# History (v2)
# ---------------------------------------------------------------------------

def merge_history(history, period, pulled_at, value_rows):
    """Replace rows for this period, append fresh ones. Sort by (period_end, period_start, node_id)."""
    ps, pe = parse_period(period)
    grain = derive_grain(ps, pe)
    kept = [r for r in history if not (r["period_start"] == ps and r["period_end"] == pe)]
    for v in value_rows:
        row = {"period_start": ps, "period_end": pe, "grain": grain,
               "pulled_at": pulled_at,
               "node_id": v["node_id"],
               "current": v["current"],
               "benchmark": v["benchmark"],
               "higher_is_better": v["higher_is_better"],
               "measured": v["measured"],
               "source": v["source"]}
        kept.append(row)
    kept.sort(key=lambda r: (r["period_end"], r["period_start"], r["node_id"]))
    return kept


def load_history(path):
    """Load v2 history.csv. If v1 format detected, archive it and return []."""
    path = Path(path)
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        first = f.readline()
    if first.startswith("date,"):
        # v1 file — archive it
        archive = path.with_name("history-v1-archive.csv")
        suffix = 2
        while archive.is_file():
            archive = path.with_name(f"history-v1-archive-{suffix}.csv")
            suffix += 1
        path.rename(archive)
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_history(path, rows):
    path = Path(path)
    tmp = path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def history_to_payload(history):
    """history rows -> {periods:[...sorted by (end,start)], values:{period_id:{node_id:{...}}}}"""
    # Collect unique periods
    seen = {}
    for r in history:
        ps, pe = r["period_start"], r["period_end"]
        pid = f"{ps}..{pe}"
        if pid not in seen:
            s = _date.fromisoformat(ps)
            e = _date.fromisoformat(pe)
            seen[pid] = {"id": pid, "start": ps, "end": pe,
                         "grain": derive_grain(ps, pe),
                         "days": (e - s).days + 1}
    periods = sorted(seen.values(), key=lambda x: (x["end"], x["start"]))

    values = {p["id"]: {} for p in periods}
    for r in history:
        pid = f"{r['period_start']}..{r['period_end']}"
        c = _num(r["current"])
        values[pid][r["node_id"]] = {
            "c": c,
            "b": _num(r["benchmark"]),
            "hib": 1 if r["higher_is_better"] != "0" else 0,
            "m": 1 if (r["measured"] == "1" or c is not None) else 0,
            "np": 1 if r["source"].strip().upper().startswith("NOT_PULLABLE") else 0,
            "src": r["source"],
            "win": pid}   # tooltip uses win — emit period id so tooltip keeps working
    return {"periods": periods, "values": values}


# ---------------------------------------------------------------------------
# Graph model loader
# ---------------------------------------------------------------------------

def load_graph_model():
    """nodes + edges + layout from skill references, normalized for the template."""
    nodes, edges = [], []
    with open(REFS / "funnel-nodes.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nodes.append({"id": r["id"], "label": r["label"],
                          "layer": LAYER_KEY[r["layer"].strip().lower()],
                          "def": r["definition"]})
    with open(REFS / "funnel-edges.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            edges.append({"s": r["source"], "t": r["target"], "w": float(r["strength"]),
                          "sign": -1 if r["direction"].strip() == "negative" else 1,
                          "lag": float(r["lag_weeks"] or 0), "type": r["type"].strip()})
    layout = json.loads((REFS / "graph-layout.json").read_text(encoding="utf-8"))
    known = {n["id"] for n in nodes}
    for nid in list(layout):
        if nid not in known:
            del layout[nid]
    return {"nodes": nodes, "edges": edges, "layout": layout}


# ---------------------------------------------------------------------------
# Block builder + injector
# ---------------------------------------------------------------------------

def build_block(client, run_period, history):
    template = (REFS / "graph-template.html").read_text(encoding="utf-8")
    model = load_graph_model()
    payload = history_to_payload(history)
    known = {n["id"] for n in model["nodes"]}
    for pid, vals in payload["values"].items():
        for nid in list(vals):
            if nid not in known:
                print(f"WARN: unknown node id '{nid}' in period {pid}; skipped", file=sys.stderr)
                del vals[nid]
    data = {"client": client, "runPeriod": run_period, **model, **payload}
    js = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")  # script-safe
    return template.replace("/*__GRAPH_DATA__*/null", js)


def inject(report_path, block):
    report_path = Path(report_path)
    if not report_path.is_file():
        raise FileNotFoundError(f"report not found: {report_path}")
    html = report_path.read_text(encoding="utf-8")
    wrapped = f"{START_MARK}\n{block}\n{END_MARK}"
    if START_MARK in html:
        html = re.sub(re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
                      lambda _m: wrapped, html, count=1, flags=re.S)
    else:
        i = html.rfind("</body>")
        if i == -1:
            raise ValueError(f"no </body> in {report_path}")
        html = html[:i] + wrapped + "\n" + html[i:]
    report_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--values", required=True)
    ap.add_argument("--period", required=True,
                    help="Compare period: YYYY-MM-DD..YYYY-MM-DD")
    ap.add_argument("--baseline-values",
                    help="Optional baseline node-values.csv (requires --baseline-period)")
    ap.add_argument("--baseline-period",
                    help="Optional baseline period: YYYY-MM-DD..YYYY-MM-DD (requires --baseline-values)")
    ap.add_argument("--client", required=True)
    ap.add_argument("--pulled-at", default=_date.today().isoformat(),
                    help="ISO date of this pull (default: today)")
    ap.add_argument("--report", required=True)
    ap.add_argument("--standalone", help="dev: also write a standalone page here")
    a = ap.parse_args(argv)

    # Validate baseline pair — both or neither
    if bool(a.baseline_values) != bool(a.baseline_period):
        print("ERROR: --baseline-values and --baseline-period must be given together",
              file=sys.stderr)
        return 2

    # Early missing-report check (before any history work)
    if not Path(a.report).is_file():
        print(f"ERROR: report not found: {a.report}", file=sys.stderr)
        return 1

    values_path = Path(a.values)
    funnel_dir = values_path.parent.parent          # clients/{C}/funnel
    history_path = funnel_dir / "history.csv"

    history = load_history(history_path)
    history = merge_history(history, a.period, a.pulled_at, read_values(values_path))
    if a.baseline_values:
        history = merge_history(history, a.baseline_period, a.pulled_at,
                                read_values(Path(a.baseline_values)))
    write_history(history_path, history)

    block = build_block(a.client, a.period, history)
    inject(a.report, block)
    n_periods = len({(r["period_start"], r["period_end"]) for r in history})
    print(f"graph injected into {a.report} ({n_periods} period(s) in history)")

    if a.standalone:
        page = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<title>Funnel graph (standalone)</title></head><body>"
                + block + "<script>document.getElementById('fg-open').click()</script>"
                "</body></html>")
        Path(a.standalone).write_text(page, encoding="utf-8")
        print(f"standalone written to {a.standalone}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never dump a raw traceback into a funnel run
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
