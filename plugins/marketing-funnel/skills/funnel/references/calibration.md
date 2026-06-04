# Calibration — three tiers, no cross-account pooling required

The skill does **not** depend on pooling many accounts to estimate universal edge strengths. That approach needs large N, washes out across industries, and isn't worth doing. Calibration here is per-account and mostly arithmetic. Three tiers:

## Tier 1 — Identity (exact, no calibration ever)
The spine and the conversion-rate / AOV chain are multiplicative arithmetic. For these levers, `score.py` computes the impact of moving current→target exactly from THIS account's own numbers:

```
Δrevenue = base × (p_target / p_current − 1)
```
where `p` is the value (or `1 − value` for negative drivers like cart abandonment) and `base` is monthly revenue (or returning revenue for retention factors). No edge strength is involved. Labelled `exact`. This covers ~60% of the actionable levers (PDP rate, add-to-cart, initiate-checkout, checkout completion, cart/checkout abandonment, units-per-order, ASP; and repeat rate / frequency / LTV when a returning-revenue baseline is given).

Caveat shown on every exact figure: it is **ceteris paribus** (holding other stages fixed) and represents the **theoretical prize of fully closing the benchmark gap**. Overlapping stages must not be summed.

## Tier 2 — Per-account longitudinal (prior, self-correcting)
The genuinely statistical edges are the minority — lagged TOF/brand/halo and retention timing. These keep the hypothesized strength as a **prior**, labelled `prior`. They are not calibrated by pooling accounts; each account calibrates its own priors over time from its own history (n = 1 account, many weeks). You only need direction and rank-order, not a precise coefficient. Heterogeneity across accounts is a reason to stay account-specific, not a problem.

## Tier 3 — Outcome tracking (the real calibration loop)
Every run logs its predictions; later you record what actually happened. The account's own track record corrects the model. This needs only the accounts you already run.

### Outcomes log — `clients/{Client}/outcomes-log.csv`
```
date,lever,method,predicted_rev,predicted_profit,target,metric_before,metric_after,actual_rev_delta,owner,status
2026-06-02,attach,prior,55987,19595,0.15,0.05,,,post-purchase.md,open
2026-04-01,checkout,exact,170000,59500,0.72,0.60,0.69,127500,low-ticket.md,closed
```
- At run time: write one `open` row per recommended lever (date, lever, method, predicted_rev/profit, target, metric_before).
- 30/60/90 days later: fill `metric_after` + `actual_rev_delta`, set `status=closed`.

### `scripts/calibrate.py` reads the log and produces, per lever, account-specific corrections:
- **prior levers** → a **strength multiplier** = median(actual ÷ predicted). Nudges that lever's hypothesized edge for THIS account. Applied next run.
- **exact levers** → an **attainment factor** = actual ÷ theoretical. Exact math gives the *max*; attainment tells you what fraction of the benchmark gap this account realistically captures (e.g., 0.6 = you tend to close 60% of a CVR gap). Future runs can show `exact × attainment` as the realistic estimate alongside the theoretical max.

Both corrections are per-account and longitudinal. Five accounts tracked over a few quarters teaches the model far more than 500 accounts pooled once — and never forces a cross-industry average onto a single brand.

## What this gives up
Only the claim that the strengths are *industry-universal*. The skill never needed that claim — the question is "what is THIS account's biggest lever," answered by identity math + this account's data + external benchmarks + its own outcome history.
