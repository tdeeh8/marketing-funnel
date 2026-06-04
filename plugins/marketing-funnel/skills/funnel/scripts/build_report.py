#!/usr/bin/env python3
"""
Build the self-contained HTML gap brief from levers.json + plays.json.

Run ONLY after verify.py exits 0. Renders: header, the answer (revenue + profit),
funnel heat strip, opportunity ladder, and a per-lever drawer with the why-chain
(target → … → revenue, from the graph), the dials to adjust (graph upstream drivers),
and the grounded plays.

Usage:
  python3 build_report.py --levers levers.json --plays plays.json --client "Acme Co" --out report.html
"""
import csv, os, json, argparse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REF  = os.path.join(HERE, "..", "references")
LCOL = {"TOF": "#7F77DD", "MOF": "#1D9E75", "BOF": "#639922", "AOV": "#BA7517",
        "Retention": "#D85A30", "Spine": "#60a5fa", "Revenue": "#f472b6"}


def graph():
    lab = {}
    for r in csv.reader(open(os.path.join(REF, "funnel-nodes.csv"))):
        if r and r[0] != "id":
            lab[r[0]] = r[1]
    inbound = collections.defaultdict(list)
    for r in csv.reader(open(os.path.join(REF, "funnel-edges.csv"))):
        if r and r[0] != "source":
            inbound[r[1]].append({"src": r[0], "label": lab.get(r[0], r[0]),
                                  "edge": "negative" if r[3] == "negative" else "positive",
                                  "strength": float(r[2]), "lag": float(r[4])})
    return lab, inbound


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levers", required=True)
    ap.add_argument("--plays", default=None)
    ap.add_argument("--client", default="Client")
    ap.add_argument("--flags", default=None,
                    help="optional JSON list of data-quality issues: [{area,status,off,missing,fix}]")
    ap.add_argument("--target", type=int, default=None,
                    help="realistic measurable-lever count for THIS account (presentation only; e.g. ~40). "
                         "Used to frame coverage against an achievable target instead of all 88 nodes.")
    ap.add_argument("--baseline-source", default=None,
                    help="label of the revenue baseline source, e.g. 'Shopify' or 'GA4'. If it is NOT a "
                         "financial-truth source (Shopify / Triple Whale / BigCommerce), every dollar figure "
                         "is flagged DIRECTIONAL in the report so a GA4-undercounted number never reads as exact.")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    TRUTH = {"shopify", "triplewhale", "triple whale", "tw", "bigcommerce"}
    bsrc = a.baseline_source
    directional = bool(bsrc) and bsrc.strip().lower() not in TRUTH

    data = json.load(open(a.levers)); meta = data["meta"]
    lab, inbound = graph()
    plays = json.load(open(a.plays)) if a.plays else []
    plays_by = collections.defaultdict(list)
    for p in plays:
        plays_by[p["lever"]].append(p)

    rev = data["revenue"]; prof = data["profit"]
    # Within each group sort by opportunity score (most actionable first); order the two
    # groups by their top score so the highest-opportunity section leads.
    okey = lambda L: -L.get("opportunity", 0)
    ex = sorted([L for L in rev if L["method"] == "exact"], key=okey)[:4]
    pr = sorted([L for L in rev if L["method"] == "prior"], key=okey)[:3]
    groups = sorted([g for g in (ex, pr) if g], key=lambda g: -g[0].get("opportunity", 0))
    top = [L for g in groups for L in g]
    rev_top = rev[0] if rev else None
    prof_top = prof[0] if prof else None

    # heat strip: opportunity per layer (sum realistic revenue)
    layer_opp = collections.defaultdict(float)
    for L in rev:
        layer_opp[L["layer"]] += L["revenue_real"]

    measured_vals = {L["id"]: L for L in rev}
    rows = []
    for L in top:
        # Dial direction = which way to PUSH the dial so this lever improves.
        # A negative edge flips the push direction relative to the lever's own direction-of-good.
        dials = []
        for d in inbound.get(L["id"], [])[:6]:
            m = measured_vals.get(d["src"])
            push_up = (L["direction"] == "increase") == (d["edge"] == "positive")
            dials.append({"id": d["src"], "label": d["label"],
                          "dir": "increase" if push_up else "reduce",
                          "edge": d["edge"], "strength": d["strength"], "lag": d["lag"],
                          "measured": bool(m),
                          "current": m["current"] if m else None,
                          "benchmark": m["benchmark"] if m else None})
        rows.append({
            "id": L["id"], "label": L["label"], "layer": L["layer"], "color": LCOL.get(L["layer"], "#888"),
            "dir": L["direction"], "current": L["current"], "benchmark": L["benchmark"],
            "rev": L["revenue_real"], "prof": L["profit_real"], "ceiling": L["revenue_usd"],
            "opp": L.get("opportunity", 0),
            "attainment": L["attainment"], "profit_note": L["profit_note"],
            "elasticity": L["elasticity"], "headroom": L["headroom"], "sensitivity": L["sensitivity"],
            "method": L["method"], "base": L["base"],
            "group": ("Fix now · exact identity math" if L["method"] == "exact" else "Invest in growth · prior estimate"),
            "source": L["source"], "window": L["window"], "confidence": L["confidence"],
            "chain": L["chain"], "dials": dials,
            "plays": [{"text": p["text"], "owner": p["owner"], "primary": p.get("primary", False),
                       "target": p["target_metric"], "intermediate": p["intermediate_metric"],
                       "outcome": p["outcome_metric"], "why": p["why"]} for p in plays_by.get(L["id"], [])],
        })

    flags = json.load(open(a.flags)) if a.flags else []
    gaps = meta.get("data_gaps", []); measured = meta.get("measured", "?")
    unlocks = len(flags)  # each passed flag is a fix/connection that unlocks more levers
    cov_off = (f"{measured} of ~{a.target} realistically-measurable levers captured this run."
               if a.target else f"{measured} levers measured live this run.")
    if unlocks:
        cov_off += f" The {unlocks} fix(es)/connection(s) below would unlock more."
    cov_flag = {"area": "Coverage",
                "status": "info",
                "off": cov_off,
                "missing": ("Highest-leverage not yet measured: " + ", ".join(g["label"] for g in gaps[:5])) if gaps else "—",
                "fix": "Work the items below to measure more. The rest of the 88-node map is qualitative or not applicable to this business — no account exposes all 88, so partial coverage is expected, not a failure."}
    all_flags = [cov_flag] + flags

    payload = {
        "client": a.client, "meta": meta, "flags": all_flags,
        "baseline_source": bsrc, "directional": directional,
        "rev_top": {"label": rev_top["label"], "layer": rev_top["layer"], "rev": rev_top["revenue_real"],
                    "cur": rev_top["current"], "bench": rev_top["benchmark"]} if rev_top else None,
        "prof_top": {"label": prof_top["label"], "layer": prof_top["layer"], "prof": prof_top["profit_real"],
                     "cur": prof_top["current"], "bench": prof_top["benchmark"]} if prof_top else None,
        "heat": [{"layer": k, "opp": round(v), "color": LCOL.get(k, "#888")} for k, v in
                 sorted(layer_opp.items(), key=lambda kv: -kv[1])],
        "rows": rows,
    }

    html = HEAD + "<script>window.DATA=" + json.dumps(payload) + ";</script>\n" + BODY + "</body></html>"
    open(a.out, "w").write(html)
    print(f"wrote {a.out} ({len(html):,} bytes, {len(rows)} levers)")


HEAD = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Funnel Gap Brief</title>
<style>
:root{--bg:#f5f7fa;--panel:#ffffff;--p2:#eef1f6;--ink:#1f2733;--mut:#5d6775;--line:#e1e6ee;--info:#2f6fd0;--green:#5a8a16;--warn:#b7791f;--shadow:0 1px 2px rgba(17,24,39,.05),0 1px 3px rgba(17,24,39,.06);}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:18px;}
.wrap{max-width:760px;margin:0 auto;}
.hd{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:12px;}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}
.card{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:10px;padding:12px 14px;}
.lbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:0 0 5px;}
.heat{display:flex;gap:10px;align-items:flex-end;height:74px;margin-bottom:16px;}
.heat .col{flex:1;text-align:center;}
.row{cursor:pointer;display:grid;grid-template-columns:1fr 150px 168px;gap:6px 12px;align-items:center;padding:6px;border-radius:8px;border-bottom:1px solid var(--line);}
.bar{flex:1;height:13px;background:var(--p2);border-radius:3px;overflow:hidden;}
.bar>div{height:100%;border-radius:3px;}
.dot{width:8px;height:8px;border-radius:2px;flex:0 0 8px;}
.draw{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:12px;padding:14px 16px;margin-top:14px;}
.blk{background:var(--p2);border-radius:8px;padding:9px 11px;}
.chain{font-size:12.5px;background:var(--p2);border-radius:8px;padding:9px 11px;line-height:1.7;}
.pill{font-size:10.5px;white-space:nowrap;padding:2px 7px;border-radius:8px;background:var(--p2);color:var(--mut);}
.play{display:flex;gap:8px;align-items:flex-start;padding:7px 9px;border-radius:8px;margin-bottom:6px;}
.foot{border-top:1px solid var(--line);margin-top:14px;padding-top:8px;font-size:11.5px;color:var(--mut);}
.bwrap{margin-bottom:14px;}
.banner{border:1px solid var(--warn);background:rgba(251,191,36,.10);border-radius:10px;padding:9px 12px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px;}
.banner.ok{border-color:var(--line);background:var(--p2);}
.bpanel{border:1px solid var(--line);border-top:none;border-radius:0 0 10px 10px;padding:2px 12px 8px;display:none;}
.bcard{padding:9px 0;border-bottom:1px solid var(--line);}
.bcard:last-child{border-bottom:none;}
.bcard .ar{font-size:13px;font-weight:500;display:flex;align-items:center;gap:7px;}
.bcard .kv{font-size:12px;color:var(--mut);margin-top:3px;}
.bcard .kv b{color:var(--ink);font-weight:500;}
.sdot{width:9px;height:9px;border-radius:50%;flex:0 0 9px;display:inline-block;}
details.blk summary{display:flex;align-items:center;gap:8px;cursor:pointer;list-style:none;}
details.blk summary::-webkit-details-marker{display:none;}
details.blk summary:after{content:'▸';color:var(--mut);font-size:10px;}
details.blk[open] summary:after{content:'▾';}
.pill.dial{cursor:pointer;}
.pill.dial:hover{background:#e3e9f3;}
.pill.dial.on{background:#dbe6f6;color:#21528f;}
</style></head><body><div class="wrap">
"""

BODY = """<div id="app"></div>
<script>
const D=window.DATA, f=n=>n==null?'—':'$'+Number(n).toLocaleString();
const gv=s=>{const n=Number(s);return (Number.isFinite(n)&&Number.isInteger(n)&&Math.abs(n)>=1000)?n.toLocaleString():s;};
let sel=0,dialOpen=-1;
function arrow(d){return d==='reduce'?'<i style="color:#e0465f">▼</i>':'<i style="color:#2f6fd0">▲</i>';}
function dialDetail(cur){
  if(dialOpen<0||!cur.dials[dialOpen])return '';
  const d=cur.dials[dialOpen];
  const rel=d.edge==='positive'?`Higher <b>${d.label}</b> pushes <b>${cur.label}</b> up`:`Higher <b>${d.label}</b> pushes <b>${cur.label}</b> down`;
  const goal=cur.dir==='reduce'?'lower':'higher';
  const act=d.dir==='increase'?`push <b>${d.label}</b> up ▲`:`bring <b>${d.label}</b> down ▼`;
  const lag=d.lag>=1?` Effect lags ~${Math.round(d.lag)} week${d.lag>=2?'s':''} — don't judge it day-to-day.`:'';
  const meas=d.measured?`Measured this run: now <b>${gv(d.current)}</b> → shoot for <b>${gv(d.benchmark)}</b>.`:`Not measured this run — no live value or target yet. Connect its data source (see the data-completeness banner) to put a number on this dial.`;
  return `<div class="blk" style="margin-top:8px;font-size:12.5px;line-height:1.65">
    <b>${arrow(d.dir)} ${d.label}</b> <span style="color:var(--mut)">· upstream driver of ${cur.label} · graph strength ${d.strength}</span><br>
    ${rel}; you want ${cur.label} ${goal}, so the move is: ${act}.${lag}<br>${meas}</div>`;
}
function conf(m){const ex=m==='exact';return `<span style="font-size:10px;padding:1px 6px;border-radius:6px;background:${ex?'rgba(90,138,22,.15)':'rgba(183,121,31,.15)'};color:${ex?'#4f7a13':'#9a6a00'}">${ex?'exact':'prior'}</span>`;}
function revMath(c){
  if(c.method==='exact'){
    const base=c.base==='ret'?'returning rev':f(D.meta.baseline);
    return `realistic ${f(c.rev)} = ceiling ${f(c.ceiling)} × ${Math.round(c.attainment*100)}% attainment · ceiling = ${base} × (${c.benchmark}/${c.current} − 1), ceteris paribus`;
  }
  return `${f(c.rev)} = ${f(D.meta.baseline)} × ${c.elasticity} elasticity × ${c.headroom} headroom · prior`;
}
function oppColor(s){return s>=66?'#5a8a16':(s>=33?'#b7791f':'#8a93a3');}
function ladder(r){let g=null,h='';r.forEach((x,i)=>{
 if(x.group!==g){h+=`<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:11px 0 4px">${x.group}</div>`;g=x.group;}
 const oc=oppColor(x.opp);
 h+=`<div class="row" onclick="sel=${i};dialOpen=-1;render()" style="background:${i===sel?'var(--p2)':'transparent'}">
   <div style="display:flex;align-items:center;gap:6px;min-width:0"><span class="dot" style="background:${x.color}"></span>
     <span style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${arrow(x.dir)} ${x.label}</span>${conf(x.method)}</div>
   <span style="font-size:12.5px;color:var(--ink)">${gv(x.current)} <span style="color:var(--mut)">→</span> ${gv(x.benchmark)}</span>
   <div style="display:flex;align-items:center;gap:8px"><div class="bar"><div style="width:${Math.max(3,x.opp)}%;background:${oc}"></div></div><span style="width:42px;text-align:right;font-size:13px;font-weight:600;color:${oc}">${x.opp}</span></div>
  </div>`;});return h;}
function banner(){
  const fl=D.flags||[]; if(!fl.length) return '';
  const unlocks=fl.filter(x=>x.area!=='Coverage').length;
  const sev=fl.some(x=>x.status==='warning'||x.status==='broken');
  const sc={broken:'#fb7185',warning:'#fbbf24',info:'#9aa4b2'};
  const head=unlocks?`${unlocks} fix${unlocks!==1?'es':''}/connection${unlocks!==1?'s':''} would unlock more levers`:'data completeness notes';
  return `<div class="bwrap">
    <div class="banner ${sev?'':'ok'}" onclick="var p=document.getElementById('bp');p.style.display=p.style.display==='block'?'none':'block'">
      <span style="display:flex;align-items:center;gap:8px;font-size:13px"><span class="sdot" style="background:${sev?'#fbbf24':'#9aa4b2'}"></span>Data completeness — ${head}</span>
      <span style="font-size:12px;color:var(--mut)">click to expand</span></div>
    <div class="bpanel" id="bp">${fl.map(x=>`<div class="bcard"><div class="ar"><span class="sdot" style="background:${sc[x.status]||'#9aa4b2'}"></span>${x.area}</div>
      <div class="kv"><b>Off / unreliable:</b> ${x.off}</div>
      <div class="kv"><b>You may be missing:</b> ${x.missing}</div>
      <div class="kv"><b>How to fix:</b> ${x.fix}</div></div>`).join('')}</div>
  </div>`;
}
function chainHtml(ch){
  if(!ch||!ch.length)return '<span style="color:var(--mut)">root lever — see plays</span>';
  let s=ch[0].from_label;
  ch.forEach(e=>{s+=` <span style="color:var(--mut)">→</span> ${e.to_label} <span style="color:var(--mut);font-size:11px">(${e.sign<0?'−':''}${e.strength}${e.lag>=1?', ~'+Math.round(e.lag)+'wk':''})</span>`;});
  return s;
}
function render(){
  const r=D.rows;
  const maxH=Math.max(...D.heat.map(h=>h.opp))||1;
  const cur=r[sel];
  document.getElementById('app').innerHTML=`
  ${banner()}
  <div class="hd"><span style="font-size:15px;font-weight:500">Funnel gap brief — ${D.client}</span>
   <span style="font-size:12px;color:var(--mut)">${D.meta.window||''} coverage ${Math.round(D.meta.coverage*100)}% · CM2 ${Math.round(D.meta.cm2*100)}% · baseline ${f(D.meta.baseline)}/mo${D.baseline_source?' ('+D.baseline_source+')':''}</span></div>
  ${D.directional?`<div style="border:1px solid rgba(183,121,31,.35);background:rgba(183,121,31,.10);border-radius:10px;padding:8px 12px;margin-bottom:14px;font-size:12.5px;color:#8a5a12">
   <b>Directional dollars.</b> The revenue baseline comes from <b>${D.baseline_source}</b>, not a financial source of truth (Shopify / Triple Whale). Every $ below is a relative-priority signal, not an exact forecast — connect Shopify to make these exact.</div>`:''}
  <div class="cards">
   <div class="card"><p class="lbl">Biggest revenue lever</p><div style="font-size:17px;font-weight:500">${D.rev_top.label} <span style="font-size:12px;color:var(--mut)">· ${D.rev_top.layer}</span></div>
     <div style="font-size:13px;color:#2f6fd0;margin-top:2px">${f(D.rev_top.rev)}/mo · ${gv(D.rev_top.cur)}→${gv(D.rev_top.bench)}</div></div>
   <div class="card"><p class="lbl">Biggest profit lever</p><div style="font-size:17px;font-weight:500">${D.prof_top.label} <span style="font-size:12px;color:var(--mut)">· ${D.prof_top.layer}</span></div>
     <div style="font-size:13px;color:#4f7a13;margin-top:2px">${f(D.prof_top.prof)}/mo · ${gv(D.prof_top.cur)}→${gv(D.prof_top.bench)}</div></div>
  </div>
  <p class="lbl">Where the opportunity sits — $/mo by funnel stage</p>
  <div class="heat">${D.heat.map(h=>`<div class="col"><div style="font-size:11px;color:var(--mut)">${f(h.opp)}</div>
     <div style="height:${Math.round(h.opp/maxH*46)}px;background:${h.color};border-radius:4px 4px 0 0"></div>
     <div style="font-size:11px;margin-top:3px">${h.layer}</div></div>`).join('')}</div>
  <p style="font-size:11px;color:var(--mut);margin:-6px 0 12px">Stages show the <b>size of prize ($/mo)</b>; the levers below score each fix <b>0–100</b> on how much room × leverage it has. Two lenses — the scores don't sum to the stage dollars. Dollar math for any lever is one click into its row.</p>
  <p style="font-size:11px;color:var(--mut);margin:0 0 6px">${arrow('increase')} = push this metric up · ${arrow('reduce')} = push it down · "Now → target" = this account's trailing-30d value → the benchmark it's scored against.</p>
  <div style="display:grid;grid-template-columns:1fr 150px 168px;gap:6px 12px;font-size:11px;color:var(--mut);margin-bottom:4px">
   <span>Lever (click for detail)</span><span>Now → target</span><span>Opportunity /100</span></div>
  ${ladder(r)}
  <div class="draw">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><span class="dot" style="background:${cur.color}"></span>
     <span style="font-size:15px;font-weight:500">${cur.label}</span>${conf(cur.method)}
     <span style="font-size:12px;color:var(--mut)">· ${cur.layer} · ${gv(cur.current)}→${gv(cur.benchmark)}</span>
     <span style="margin-left:auto;font-size:12px;font-weight:600;color:${oppColor(cur.opp)}">opportunity ${cur.opp}/100</span></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
      <details class="blk"><summary><span class="lbl" style="margin:0">Revenue math</span><span style="margin-left:auto;font-size:12px;color:var(--mut)">${f(cur.rev)}/mo</span></summary><div style="font-size:12.5px;margin-top:7px">${revMath(cur)}</div></details>
      <details class="blk"><summary><span class="lbl" style="margin:0">Profit math</span><span style="margin-left:auto;font-size:12px;color:var(--mut)">${cur.prof==null?'—':f(cur.prof)+'/mo'}</span></summary><div style="font-size:12.5px;margin-top:7px">${cur.prof==null?'needs incremental-spend input ('+cur.profit_note+')':f(cur.prof)+' = '+f(cur.rev)+' × '+Math.round(D.meta.cm2*100)+'% CM2 − cost'}</div></details>
      <details class="blk"><summary><span class="lbl" style="margin:0">Source</span><span style="margin-left:auto;font-size:12px;color:var(--mut)">${cur.window}</span></summary><div style="font-size:12.5px;margin-top:7px">${cur.source} · ${cur.window}</div></details>
      <details class="blk"><summary><span class="lbl" style="margin:0">Confidence</span><span style="margin-left:auto;font-size:12px;color:var(--mut)">${cur.confidence}</span></summary><div style="font-size:12.5px;margin-top:7px">${cur.confidence} · opportunity ${cur.opp}/100 = headroom ${cur.headroom} × sensitivity ${cur.sensitivity} (fixed anchor)</div></details>
    </div>
    <p class="lbl" style="margin-top:12px">Why it moves revenue (from the graph)</p>
    <div class="chain">${chainHtml(cur.chain)}</div>
    <p class="lbl" style="margin-top:12px">Dials to adjust (upstream drivers) <span style="text-transform:none;letter-spacing:0">— the inputs that move ${cur.label}; arrow = which way to push. Click a dial for context.</span></p>
    <div style="display:flex;flex-wrap:wrap;gap:6px">${cur.dials.length?cur.dials.map((d,j)=>`<span class="pill dial ${j===dialOpen?'on':''}" onclick="dialOpen=dialOpen===${j}?-1:${j};render()">${arrow(d.dir)} ${d.label}</span>`).join(''):'<span style="color:var(--mut);font-size:12px">root lever — move it through the plays below</span>'}</div>
    ${dialDetail(cur)}
    <p class="lbl" style="margin-top:12px">Plays from your current setup</p>
    ${cur.plays.length?cur.plays.map(p=>`<div class="play" style="${p.primary?'background:rgba(47,111,208,.10);border:1px solid rgba(47,111,208,.25)':'border:1px solid var(--line)'}">
      <div style="flex:1"><div style="font-size:12.5px;${p.primary?'color:#21528f;font-weight:500':''}">${p.text}</div>
        <div style="font-size:11px;color:var(--mut);margin-top:3px">${p.target} <span>→</span> ${p.intermediate} <span>→</span> ${p.outcome} — ${p.why}</div></div>
      <span class="pill">${p.owner}</span></div>`).join(''):'<span style="color:var(--mut);font-size:12px">No play generated — connect campaign/flow inventory.</span>'}
  </div>
  <div class="foot">Every number cites its source pull; every "why" is a verified graph edge; every play names only live entities. Strengths hypothesized until cross-account calibration.</div>`;
}
render();
</script>
"""

if __name__ == "__main__":
    main()
