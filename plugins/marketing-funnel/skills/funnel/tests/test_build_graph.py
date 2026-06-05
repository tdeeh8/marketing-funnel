import csv, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_graph as bg

VALS_HEADER = "id,current,benchmark,higher_is_better,measured,source,window,incr_spend\n"

PERIOD_W1 = "2026-05-18..2026-05-24"   # Mon..Sun -> week
PERIOD_W2 = "2026-05-25..2026-05-31"   # Mon..Sun -> week
PERIOD_AH = "2026-05-01..2026-05-31"   # -> adhoc


def mk_values(tmp_path, date, rows, client="Acme", name="node-values.csv"):
    d = tmp_path / "clients" / client / "funnel" / date
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(VALS_HEADER + "".join(rows))
    return d / name


# ---------------------------------------------------------------------------
# read_values (unchanged surface — keep these)
# ---------------------------------------------------------------------------

def test_read_values_tolerates_extra_cols_and_unmeasured(tmp_path):
    p = mk_values(tmp_path, "2026-06-04", [
        "ctr,0.04,0.01,1,1,meta:ctr,2026-05..2026-06,\n",
        "hook,,0.35,1,0,DATA_NOT_AVAILABLE,,\n",
    ])
    rows = bg.read_values(p)
    assert rows[0]["node_id"] == "ctr" and rows[0]["current"] == "0.04"
    assert rows[1]["measured"] == "0" and rows[1]["current"] == ""


# ---------------------------------------------------------------------------
# derive_grain and parse_period
# ---------------------------------------------------------------------------

def test_derive_grain():
    assert bg.derive_grain("2026-05-25", "2026-05-31") == "week"   # Mon..Sun, 7d
    assert bg.derive_grain("2026-05-01", "2026-05-31") == "adhoc"
    assert bg.derive_grain("2026-05-26", "2026-06-01") == "adhoc"  # Tue..Mon, 7d but not calendar week


def test_parse_period():
    assert bg.parse_period(PERIOD_W2) == ("2026-05-25", "2026-05-31")
    import pytest
    with pytest.raises(ValueError): bg.parse_period("2026-06-01..2026-05-01")  # reversed
    with pytest.raises(ValueError): bg.parse_period("not-a-period")


# ---------------------------------------------------------------------------
# merge_history (period-keyed)
# ---------------------------------------------------------------------------

def test_merge_history_keyed_by_period(tmp_path):
    p = mk_values(tmp_path, "run", ["ctr,0.04,0.01,1,1,meta:ctr,w,\n"])
    rows = bg.read_values(p)
    h = bg.merge_history([], PERIOD_W2, "2026-06-05", rows)
    h = bg.merge_history(h, PERIOD_W2, "2026-06-06", rows)        # re-pull same period -> replace
    assert len(h) == 1 and h[0]["pulled_at"] == "2026-06-06" and h[0]["grain"] == "week"
    h = bg.merge_history(h, PERIOD_W1, "2026-06-06", rows)        # second period -> adds
    assert len(h) == 2


# ---------------------------------------------------------------------------
# load_history (v1 archive + v2 roundtrip)
# ---------------------------------------------------------------------------

def test_load_history_archives_v1(tmp_path):
    hp = tmp_path / "history.csv"
    hp.write_text("date,node_id,current,benchmark,higher_is_better,measured,source,window\n"
                  "2026-06-04,ctr,0.04,0.01,1,1,meta:ctr,w\n", encoding="utf-8")
    assert bg.load_history(hp) == []
    assert (tmp_path / "history-v1-archive.csv").is_file()
    assert not hp.is_file()


def test_history_v2_roundtrip(tmp_path):
    p = mk_values(tmp_path, "run", ["ctr,0.04,0.01,1,1,\"meta:ctr,acct\",w,\n"])
    h = bg.merge_history([], PERIOD_W2, "2026-06-05", bg.read_values(p))
    hp = tmp_path / "history.csv"
    bg.write_history(hp, h)
    assert bg.load_history(hp) == h


# ---------------------------------------------------------------------------
# payload (period-keyed)
# ---------------------------------------------------------------------------

def test_payload_periods_and_values():
    rows = [{"node_id": "ctr", "current": "0.04", "benchmark": "0.01",
             "higher_is_better": "1", "measured": "1", "source": "meta:ctr", "window": ""}]
    h = bg.merge_history([], PERIOD_W1, "2026-06-05", rows)
    h = bg.merge_history(h, PERIOD_W2, "2026-06-05", rows)
    h = bg.merge_history(h, PERIOD_AH, "2026-06-05", rows)
    p = bg.history_to_payload(h)
    ids = [x["id"] for x in p["periods"]]
    assert ids == [PERIOD_W1, PERIOD_AH, PERIOD_W2]            # sorted by end, then start
    g = {x["id"]: x["grain"] for x in p["periods"]}
    assert g[PERIOD_W1] == "week" and g[PERIOD_AH] == "adhoc"
    assert {x["id"]: x["days"] for x in p["periods"]}[PERIOD_AH] == 31
    v = p["values"][PERIOD_W2]["ctr"]
    assert v["c"] == 0.04 and v["m"] == 1 and v["np"] == 0


# ---------------------------------------------------------------------------
# np flag re-expressed against a period
# ---------------------------------------------------------------------------

def test_history_to_payload_flags_not_pullable():
    rows_quiz = [{"node_id": "quiz", "current": "DATA_NOT_AVAILABLE", "benchmark": "",
                  "higher_is_better": "1", "measured": "0",
                  "source": "NOT_PULLABLE: no quiz on site", "window": "w"}]
    rows_ctr  = [{"node_id": "ctr", "current": "0.04", "benchmark": "0.01",
                  "higher_is_better": "1", "measured": "1", "source": "meta:ctr", "window": "w"}]
    h = bg.merge_history([], PERIOD_W2, "2026-06-05", rows_quiz + rows_ctr)
    v = bg.history_to_payload(h)["values"][PERIOD_W2]
    assert v["quiz"]["np"] == 1 and v["quiz"]["m"] == 0
    assert v["ctr"]["np"] == 0


# ---------------------------------------------------------------------------
# volume metric (no benchmark) re-expressed against a period
# ---------------------------------------------------------------------------

def test_history_to_payload_tracks_no_benchmark_volume_metrics():
    rows = [
        {"node_id": "tof_spend", "current": "70755", "benchmark": "",
         "higher_is_better": "1", "measured": "0",
         "source": "databox:FbAds@spend", "window": "2026-05"},
        {"node_id": "ic_rate", "current": "DATA_NOT_AVAILABLE", "benchmark": "",
         "higher_is_better": "1", "measured": "0",
         "source": "broken event", "window": "2026-05"},
    ]
    h = bg.merge_history([], PERIOD_W2, "2026-06-04", rows)
    v = bg.history_to_payload(h)["values"][PERIOD_W2]
    assert v["tof_spend"]["m"] == 1 and v["tof_spend"]["c"] == 70755.0 and v["tof_spend"]["b"] is None
    assert v["ic_rate"]["m"] == 0 and v["ic_rate"]["c"] is None


# ---------------------------------------------------------------------------
# write_history / non-ascii / atomic write (surface unchanged; v2 fields)
# ---------------------------------------------------------------------------

def test_write_history_ignores_extra_keys_and_preserves_file(tmp_path):
    hp = tmp_path / "history.csv"
    h = bg.merge_history([], PERIOD_W2, "2026-06-05",
                         [{"node_id": "ctr", "current": "0.03", "benchmark": "0.01",
                           "higher_is_better": "1", "measured": "1",
                           "source": "meta:ctr", "window": "w"}])
    bg.write_history(hp, h)
    h_extra = [dict(h[0], stray_column="boom")]
    bg.write_history(hp, h_extra)          # must not raise, must not truncate
    out = bg.load_history(hp)
    assert len(out) == 1 and out[0]["node_id"] == "ctr"
    assert not (tmp_path / "history.csv.tmp").exists()


def test_history_non_ascii_roundtrip(tmp_path):
    hp = tmp_path / "history.csv"
    h = bg.merge_history([], PERIOD_W2, "2026-06-05",
                         [{"node_id": "ctr", "current": "0.04", "benchmark": "0.01",
                           "higher_is_better": "1", "measured": "1",
                           "source": "meta:ctr — émdash", "window": "w"}])
    bg.write_history(hp, h)
    assert bg.load_history(hp)[0]["source"] == "meta:ctr — émdash"


# ---------------------------------------------------------------------------
# load_graph_model (unchanged)
# ---------------------------------------------------------------------------

def test_load_graph_model_normalizes_layers_and_signs():
    m = bg.load_graph_model()
    assert len(m["nodes"]) == 88 and len(m["edges"]) == 123
    layers = {n["layer"] for n in m["nodes"]}
    assert layers == {"tof", "mof", "bof", "aov", "ret", "spine", "out"}
    assert {e["sign"] for e in m["edges"]} == {1, -1}
    assert len(m["layout"]) == 88


# ---------------------------------------------------------------------------
# inject (unchanged)
# ---------------------------------------------------------------------------

def test_inject_inserts_before_body(tmp_path):
    rp = tmp_path / "report.html"
    rp.write_text("<html><body><p>report</p></body></html>")
    bg.inject(rp, "<div id='fg'>BLOCK</div>")
    t = rp.read_text()
    assert bg.START_MARK in t and bg.END_MARK in t
    assert t.index("BLOCK") < t.index("</body>")


def test_inject_idempotent_replaces_block(tmp_path):
    rp = tmp_path / "report.html"
    rp.write_text("<html><body></body></html>")
    bg.inject(rp, "v1")
    bg.inject(rp, "v2")
    t = rp.read_text()
    assert t.count(bg.START_MARK) == 1 and "v2" in t and "v1" not in t


# ---------------------------------------------------------------------------
# main() (v2 CLI — --period instead of --date)
# ---------------------------------------------------------------------------

def test_main_missing_report_exits_nonzero(tmp_path):
    p = mk_values(tmp_path, "run", ["ctr,0.04,0.01,1,1,meta:ctr,w,\n"])
    rc = subprocess.run([sys.executable, str(Path(bg.__file__)),
                         "--values", str(p), "--client", "Acme",
                         "--period", PERIOD_W2,
                         "--report", str(tmp_path / "nope.html")]).returncode
    assert rc != 0


# ---------------------------------------------------------------------------
# verify.py coverage (unchanged — verify reads node-values.csv, not history)
# ---------------------------------------------------------------------------

import subprocess as _sp


def _verify_cmd(values_path, tmp_path):
    """Run verify.py with minimal valid companion files."""
    import json as _json
    levers = tmp_path / "levers.json"; plays = tmp_path / "plays.json"; inv = tmp_path / "inventory.csv"
    levers.write_text(_json.dumps({"meta": {"baseline": 100000, "ret_baseline": 10000}, "revenue": []}))
    plays.write_text("[]"); inv.write_text("entity_id,type,name,attrs\n")
    scripts = Path(bg.__file__).parent
    return _sp.run([sys.executable, str(scripts / "verify.py"),
                    "--values", str(values_path), "--levers", str(levers),
                    "--plays", str(plays), "--inventory", str(inv)],
                   capture_output=True, text=True)


def test_verify_fails_on_incomplete_node_coverage(tmp_path):
    p = mk_values(tmp_path, "2026-06-05", ["ctr,0.04,0.01,1,1,meta:ctr,w,\n"])  # 1 of 88
    r = _verify_cmd(p, tmp_path)
    assert r.returncode != 0
    assert "missing" in (r.stdout + r.stderr).lower()


def test_verify_passes_on_full_coverage(tmp_path):
    import csv as _csv
    refs = Path(bg.__file__).parent.parent / "references" / "funnel-nodes.csv"
    ids = [row["id"] for row in _csv.DictReader(open(refs))]
    rows = [f"{i},DATA_NOT_AVAILABLE,,1,0,NOT_PULLABLE: test,w,\n" for i in ids]
    rows[0] = f"{ids[0]},0.04,0.01,1,1,meta:ctr,w,\n"
    p = mk_values(tmp_path, "2026-06-05", rows)
    r = _verify_cmd(p, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


# ---------------------------------------------------------------------------
# payload win field + CLI baseline half-pair (Task 1 review riders)
# ---------------------------------------------------------------------------

def test_payload_win_equals_period_id(tmp_path):
    p = mk_values(tmp_path, "run", [
        "ctr,0.04,0.01,1,1,meta:ctr,w,\n",
        "hook,,0.35,1,0,DATA_NOT_AVAILABLE,,\n",
    ])
    rows = bg.read_values(p)
    h = bg.merge_history([], PERIOD_W1, "2026-06-05", rows)
    h = bg.merge_history(h, PERIOD_W2, "2026-06-05", rows)
    payload = bg.history_to_payload(h)
    for pid, vals in payload["values"].items():
        for node_id, v in vals.items():
            assert v["win"] == pid, f"{node_id} in {pid} has win={v['win']!r}"


def test_main_baseline_half_pair_exits_nonzero(tmp_path):
    p = mk_values(tmp_path, "run", ["ctr,0.04,0.01,1,1,meta:ctr,w,\n"])
    rp = tmp_path / "report.html"
    rp.write_text("<html><body></body></html>")
    rc = subprocess.run([sys.executable, str(Path(bg.__file__)),
                         "--values", str(p), "--client", "Acme",
                         "--period", PERIOD_W2,
                         "--baseline-values", str(p),       # no --baseline-period
                         "--report", str(rp)]).returncode
    assert rc != 0


# ---------------------------------------------------------------------------
# verify.py values-only mode (Fix 1 — --levers/--plays/--inventory optional)
# ---------------------------------------------------------------------------

def test_verify_values_only_mode(tmp_path):
    import csv as _csv
    refs = Path(bg.__file__).parent.parent / "references" / "funnel-nodes.csv"
    ids = [row["id"] for row in _csv.DictReader(open(refs))]
    rows = [f"{i},DATA_NOT_AVAILABLE,,1,0,NOT_PULLABLE: test,w,\n" for i in ids]
    p = mk_values(tmp_path, "2026-06-05", rows)
    scripts = Path(bg.__file__).parent
    r = _sp.run([sys.executable, str(scripts / "verify.py"), "--values", str(p)],
                capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    # incomplete file still fails in values-only mode
    p2 = mk_values(tmp_path, "2026-06-06", ["ctr,0.04,0.01,1,1,meta:ctr,w,\n"])
    r2 = _sp.run([sys.executable, str(scripts / "verify.py"), "--values", str(p2)],
                 capture_output=True, text=True)
    assert r2.returncode != 0
