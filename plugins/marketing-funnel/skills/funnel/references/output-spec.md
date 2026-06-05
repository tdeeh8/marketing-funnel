# Output Spec — the gap brief

The deliverable is a single self-contained HTML file (`clients/{Client}/funnel/{date}/report.html`), built by `scripts/build_report.py` from `levers.json` + `plays.json`. One screen; every element load-bearing. Do not hand-write the HTML — the script renders it deterministically so it can't drift from the data.

## Layout (six elements, in order)

1. **Header** — client · window · coverage% · CM2% · baseline $/mo. Establishes trust and reproducibility.
2. **The answer** — two cards: biggest revenue lever and biggest profit lever, each in $/mo with current→target. They usually differ; that contrast is the headline.
3. **Funnel heat strip** — five layer columns sized by total opportunity ($). This is the **size-of-prize lens**: where the money concentrates by funnel stage, in $/mo. A caption states explicitly that these stage dollars and the per-lever scores below are two different lenses and do not sum.
4. **Opportunity ladder** — top levers, grouped into "Fix now · exact" and "Invest in growth · prior". Each row: layer dot · direction arrow · lever · **now → target** (the current value and the benchmark/growth target) · **opportunity score (0–100)** with a bar. No dollar figures on the row — the $ math lives one click down in the drawer. This is the **what-to-do lens**. Rows are sorted by opportunity within each group, and the two groups are ordered by their top score so the highest-opportunity section leads. Click a row to open its drawer.
   - **Opportunity score** = `100 × headroom × |sensitivity| / anchor`, capped at 100, on a **fixed** anchor (default 0.8 via `--score-anchor`) — NOT normalized to the top lever of the run, so a 78 means the same thing across runs and clients. It is the same Headroom × Sensitivity that drives the dollars, expressed as a low-false-precision unit. A maxed/healthy lever (no headroom) scores 0 and sinks to the bottom. Score colour: green ≥66, amber 33–65, grey <33.
5. **Drawer (per lever)** — opens on click. This is where the dollar figures live (demoted from the row):
   - Revenue math + Profit math (the formula with this lever's inputs), tagged exact vs directional.
   - Source + window, and Confidence + the opportunity-score decomposition (headroom × sensitivity).
   - **Why it moves revenue** — the graph-derived chain `lever → … → REVENUE` with each edge's strength and lag. This is the "learn as you go" core.
   - **Dials to adjust** — the lever's upstream drivers from the graph (with increase/reduce direction). Root levers show "move it through the plays."
   - **Plays from your current setup** — the grounded plays, each with its `target → intermediate → outcome — why` line and the owning arm.
6. **Footer** — the grounding statement + data gaps + calibration caveat.

## The why-chain (required on every lever and every play)

Format, rendered from the graph (never authored by hand):

```
Adjust [target metric] → moves [intermediate metric] → lifts [outcome metric]
  because [edge rationale: identity = math; signal = correlation, with strength & lag]
```

Example (cross-sell attach): `attach → AOV → REVENUE` — "more cross-sell adds units per order, raising AOV, which is a direct multiplier of revenue." The lever drawer shows the full dominant path; each play shows its own `target → intermediate → outcome`.

## Build order (enforced)

```
score.py  → levers.json      (sensitivity, $, chains)
[model generates plays.json from inventory + chunk, per play-generation.md]
verify.py → MUST exit 0      (the gate)
build_report.py → report.html   (only if verify passed)
```

`build_report.py` must never run on an unverified levers/plays set. The SKILL.md workflow wires this sequence; do not skip the gate.

## Medium

Primary: the HTML one-pager (reopens, self-contained, no server). For client-facing sharing, the same content can be exported to PDF via the `/ads` reportlab pipeline — but the HTML is the source of truth.

## Embedded live graph (Step 4.6)
`report.html` carries a self-contained graph block between `<!-- FUNNEL_GRAPH_START/END -->` markers: a fixed bottom-right "Funnel graph" button opening a full-screen light overlay (report theme untouched). It embeds the full period history for the client as inline JSON; two sidebar dropdowns (Baseline / Compare) list **periods** (`YYYY-MM-DD .. YYYY-MM-DD`), not individual pulls — canonical weeks appear in a "Weeks" optgroup, ad-hoc ranges in a "⚠ Ad-hoc" optgroup. Period selection rules (enforced in the picker): same-grain only (week↔week, adhoc↔adhoc); baseline `period_end` must be strictly before compare `period_start` (no overlap); for ad-hoc pairs, lengths must be within ±10%. Options violating these rules are disabled. A sidebar Changes panel lists every mover with its Δ% between the selected periods.

Node encoding: gray dashed ghost = not tracked; fill opacity = health vs benchmark; green/red outer ring = direction-adjusted improvement/decline; blue dot = newly tracked; tooltip cites both periods' values, Δ%, benchmark, source, window. The delta floor is per-node noise floor, learned from the node's own weekly history; the tooltip appends the noise floor to the Δ line (e.g. "(noise floor ±9.4%)") so a suppressed move is never invisible. Tracked = the period recorded a numeric value (benchmark optional). Edges render only between tracked nodes; a sidebar toggle reveals unmeasured context edges at low opacity. Nodes whose source is prefixed NOT_PULLABLE render as dormant: hidden by default, revealed by clicking a node they influence, or all at once via the "show non-pullable nodes" checkbox. They remain levers in the data model. Layout is canonical (`references/graph-layout.json`) so the map is identical across clients and weeks. Built by `scripts/build_graph.py`; idempotent on re-runs. A "color nodes by change" toggle recolors tracked nodes by verdict (green improved, red declined, gray flat, blue newly tracked) instead of funnel-layer colors. First period → no rings, note reads "No comparable prior period yet."
