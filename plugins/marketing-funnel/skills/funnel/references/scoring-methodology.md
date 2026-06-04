# Scoring Methodology

## The formula

Each measured lever gets a revenue $ and a profit $, computed one of two ways depending on the lever (full detail in `calibration.md`):

- **Exact** (identity / conversion-rate / AOV factor levers): `Δrevenue = base × (target/current − 1)` — straight arithmetic from this account's own numbers, no edge strength. This is the **ceiling**: the theoretical prize of fully closing the benchmark gap, ceteris paribus (don't sum overlapping stages). The report leads with the **realistic** figure = `ceiling × attainment` (default 35%; the outcomes log calibrates a per-lever attainment factor over time). Especially at high AOV, a mass-market benchmark makes the ceiling wildly optimistic — realistic is the number to act on, ceiling is context. (Live example: one high-AOV account's checkout ceiling was $106K vs realistic ~$37K.)
- **Prior** (lagged / statistical levers): `revenue $ = baseline × elasticity × headroom`, where `elasticity = graph sensitivity × k`. Hypothesized, and self-correcting per account via the outcomes log.

Profit $ = `revenue $ × CM2 − incremental media cost`. Two rankings (revenue, profit) come out side by side, and exact vs prior are shown as separate tracks in the report because a full-gap-closure number and an estimate aren't directly comparable.

## Sensitivity — how much revenue moves per unit of the lever

Computed once from the graph (`funnel-edges.csv`), independent of any account. It is the lever's **total causal pull on revenue**, summed over every directed path to `revenue`, including the slow, lagged, and looping ones.

Formally, define influence I where `I[revenue] = 1` and for every other node `I[n] = Σ over out-edges (n→m) of w_signed(n,m) · I[m]`, solved by fixed-point iteration (converges because edge weights < 1). `Sensitivity(L) = |I[L]|`; the sign of `I[L]` tells the direction (positive = increasing the lever lifts revenue; negative = the lever is a drag, so the action is to REDUCE it — e.g., cart abandonment, return rate).

**Why this is the long-run number:** because it sums the *entire* downstream path — including `brand → branded search → sessions` (lagged 5 wk), the `LTV → prospecting → …` reinvestment loop, and the `reviews → trust/SOV → …` loop — compounding upstream and retention levers get full credit. That is what stops the system from collapsing onto bottom-funnel "profit nodes." (A short-run variant would discount lagged edges; this skill uses the undiscounted long-run version by default.)

> Sensitivity uses hypothesized edge strengths today. It is directional, not precise, until cross-account calibration replaces the strengths with measured coefficients. The *structure* (which levers are high-leverage and in what direction) is stable; the exact ordering sharpens with data.

## Headroom — how much room this account has to improve the lever

This is the account-specific half. For a lever with current value `c` and benchmark ceiling `b`:

- **higher-is-better lever:** `Headroom = max(0, (b − c) / b)` — how far below the ceiling.
- **lower-is-better lever** (negative drivers): `Headroom = max(0, (c − b) / c)` — how far above the good threshold (room to bring it down).

Headroom is clamped to [0, 1]. A lever already at or past its benchmark has ~0 headroom and drops out of the ranking no matter how high its sensitivity — you can't squeeze a maxed lever. This is the crucial account-specific filter: **sensitivity says what *could* matter; headroom says what *can still move here*.**

## Profit — real margin dollars

Profit $ = `revenue $ × CM2 − incremental media cost`. Margin levers (CRO, AOV, retention, organic, list/email) carry no incremental media spend, so their profit is `revenue $ × CM2`. Paid-acquisition levers (spend, reach, frequency, CPM, CPC) carry a media cost: profit needs an `incr_spend` input, and without it the report shows profit as `—` rather than faking it. This is why revenue and profit rankings disagree — paid scaling can top revenue while CRO/AOV/retention top profit, because the paid lever's margin is eaten by its own spend.

CM2% comes from `clients/{Client}/CLAUDE.md`. Without it, run revenue mode only and say so.

## What gets ranked

Only **measured** levers (a real value was pulled). Unmeasured/`DATA_NOT_AVAILABLE` nodes are excluded and surfaced in a coverage note — if a high-sensitivity node is unmeasured, closing that data gap is itself a recommendation. By default the ranking focuses on **actionable input levers** (the exogenous knobs) plus any mid-funnel node with headroom; pure identity-spine nodes (revenue, orders) are outputs, not levers, and are shown for context only.

## Output contract

`score.py` emits, for each mode (revenue, profit):
- the single top lever (label, layer, direction, current vs benchmark, sensitivity, headroom, impact),
- the top N table,
- and a coverage figure (measured nodes / mappable nodes).
