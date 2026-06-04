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
