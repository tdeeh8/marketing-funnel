---
name: funnel-prioritizer
description: "Whole-funnel revenue/profit lever prioritizer with built-in anti-hallucination grounding. Pulls live metrics (Databox, Triple Whale, GA4, Klaviyo, Meta) + live campaign/flow/offer inventory, scores every lever by Headroom × Sensitivity across the entire funnel (TOF→MOF→BOF→AOV→Retention), and returns the biggest lever for long-run revenue AND profit — each with a graph-verified causal chain (which dial → which metric → which outcome → why) and grounded plays tied to the account's actual campaigns. A verification gate fails the run on any ungrounded number, dollar, causal claim, or invented entity. Use when the user runs /funnel, /lever, /biggest-lever, or asks 'what's my biggest lever', 'where should I focus to grow revenue/profit', 'what should I fix first', 'full-funnel analysis', 'what's the biggest opportunity', or 'how do I make an impact' for a DTC brand or client."
argument-hint: "[client] | revenue | profit | explain | diagnose <metric>"
license: MIT
---

# Funnel Prioritizer — the whole-funnel "biggest lever" brain

> One command: `/funnel [client]` (aliases `/lever`, `/biggest-lever`). Finds the single highest-impact lever across the ENTIRE funnel for revenue and profit, explains *why* it matters with a graph-verified causal chain, proposes plays grounded in the account's live setup, and hands execution to the right arm. It is the dispatcher; `/ads` and the playbook chunks are the execution arms.

It answers one question, with receipts: *given where this account actually is, what is the biggest lever to grow revenue (and profit) long-run — what do I change, what will it move, and why?*

## The model

**Impact = Headroom × Sensitivity**, in dollars, two ways (revenue, profit):
- **Sensitivity** = the lever's total causal pull on revenue across every graph path, including lagged/compounding loops — this gives long-run credit to brand, list, and retention levers (computed by `scripts/score.py`).
- **Headroom** = distance from the lever's CURRENT value (live pull) to its benchmark ceiling. High-leverage but maxed = low priority.
- **Revenue $** is computed two ways and each lever is labelled: **exact** for identity / conversion-rate / AOV levers — `base × (target/current − 1)` straight from this account's own numbers, no edge strength — and **prior** for lagged/statistical levers — `baseline × elasticity × headroom`. Exact levers carry a **ceiling** (full benchmark attainment) and a **realistic** figure (`ceiling × attainment`, default 35%, self-calibrated per account by the outcomes log); the report and headline lead with realistic, ceiling shown as secondary. **Profit $** = revenue $ × CM2 − incremental media cost. No cross-account pooling is needed; see `references/calibration.md`.

## Non-negotiable: grounding (read `references/grounding-rules.md`)

Every output traces to a real pull or a verified graph edge. `scripts/verify.py` enforces this and **must exit 0 before any report is built**:
- no number without a `source` + `window`;
- no dollar that doesn't recompute from the formula;
- no "why" that isn't a real graph edge;
- no play that names a campaign/flow/offer absent from the pulled inventory;
- every recommendation carries a `target → intermediate → outcome` chain.

If you cannot pull a value, write `DATA_NOT_AVAILABLE` and exclude it — never estimate, never fill from "typical brands."

## Mode detection

| User says | Mode | Action |
|---|---|---|
| `/funnel [client]` | Prioritize (default) | Full run → grounded gap brief (revenue + profit) → handoff |
| `/funnel revenue\|profit [client]` | Prioritize (one ranking) | Same, single mode |
| `/funnel diagnose <metric> [client]` | Diagnose | One metric off → upstream walk to root levers (`references/funnel-diagnostic.md`) |
| `/funnel explain` | Explain | Model + structural sensitivity ranking, no data pull |
| "what's my biggest lever", "how do I make an impact", "where should I focus" | (→ Prioritize) | Natural-language fallback |

No client named → ask the user which client/brand.

## Step 0 — Resolve client + memory
Slug the client (PascalCase-With-Dashes, e.g. `Acme-Co` — same `clients/{Client-Name}/` workspace-root convention as the audit skills; all run artifacts land in `clients/{Client}/funnel/{date}/`). Read `clients/{Client}/CLAUDE.md`. Pull AOV tier (benchmark row), CM2%/MER (profit mode), known data quirks. **Also read `clients/{Client}/playbook-config.json` / `audit-config.json`** — they hold the `databox_account_id`, the per-platform `*_data_source_id` (Shopify, GA4, Google, Meta), AOV tier, and CM2. This is how you pull live without guessing IDs, and it's the fallback when no CLAUDE.md exists.

### Step 0.1 — Bootstrap on first run (no folder system yet? create it — idempotent)
If `clients/{Client}/` (or the whole `clients/` tree) doesn't exist, BUILD it rather than erroring — same self-bootstrapping behavior as the audit skills, so a brand-new machine works on run one:
1. `mkdir -p clients/{Client}/funnel` (workspace root, PascalCase-With-Dashes).
2. **Discover the data-source IDs instead of asking for them**: Databox `list_accounts` → match the client by account name (ask the user to pick if ambiguous) → `list_data_sources(account_id)` → record the Shopify/GA4/Google/Meta data-source IDs.
3. Ask the user only what can't be discovered: AOV tier (or compute it live from Shopify totalsales ÷ orders once sources are known), CM2% (skip → revenue mode only), target MER/CAC if known.
4. Write `clients/{Client}/audit-config.json` with what you found (same schema the audit skills use — they'll reuse it), and a stub `clients/{Client}/CLAUDE.md` with a `## Snapshot`, `## Hard Constraints (confirm)`, and empty `## Recurring Patterns` section.
5. Create `clients/{Client}/outcomes-log.csv` with the header row only.
Never ask the user to manually create folders or hunt for IDs the MCP can list. Re-runs must not overwrite an existing config/CLAUDE.md — only fill gaps.

## Step 1 — Pull live values (with provenance)
Load `references/data-layer.md` + `references/node-metric-map.md`. For each mapped node, pull its current value from the right MCP and record `source` (metric key) + `window`. **Source-of-truth priority for the funnel/identity nodes** (revenue, orders, AOV, CVR, checkout completion, cart abandonment, units): **Shopify > Triple Whale > GA4** — these are financial truth and do not depend on paid attribution. Use GA4 for on-site behavior, and GA4/CAPI for channel attribution only. Always prefer a live pull over a prior audit's cached numbers; only fall back to the latest audit if the live source is unavailable, and label the window accordingly. **For Meta, check the Meta Ads MCP FIRST** (`ads_get_ad_accounts` → match the client → insights/creative tools) — it exposes hold, watch time, %-new-audience, active-creative count, and retargeting-pool size that Databox `FbAds@*` can't; fall back to Databox FbAds only if the Meta account isn't reachable there. Write `clients/{Client}/funnel/{date}/node-values.csv` (`id,current,benchmark,higher_is_better,measured,source,window[,incr_spend]`). Benchmarks from `references/benchmarks.md` by AOV tier. Save raw pulls to `clients/{Client}/funnel/{date}/evidence/`. Null → `DATA_NOT_AVAILABLE` (measured=0).

## Step 1.1 — Pull live inventory
For the lever domains likely to surface, pull campaign/flow/offer inventory → `clients/{Client}/funnel/{date}/inventory.csv` (`entity_id,type,name,attrs`). This is the grounding set for plays (see `references/play-generation.md`).

## Step 1.5 — Selective data gate (funnel vs attribution — do NOT over-block)
Two different data questions, gated separately. A broken paid pixel must NOT block the whole brief.

1. **Funnel / financial truth — Shopify is the source of truth.** Revenue, orders, AOV, sitewide CVR (orders ÷ sessions), checkout completion, cart abandonment, units-per-order come from Shopify (or BigCommerce / Triple Whale) and are reliable **even when channel attribution is broken**. If Shopify is connected and its orders reconcile, the **exact funnel levers run** regardless of GA4/CAPI paid coverage. If no Shopify / financial source is connected, you have no clean funnel ground — say so and mark funnel values low-confidence or `DATA_NOT_AVAILABLE` until it's connected. **This — not CAPI — is the only hard STOP.**
2. **Channel attribution — GA4 / CAPI.** Paid coverage and CAPI match only govern *which channel gets credit*. If coverage <70% or CAPI is >15% off Shopify, flag the **channel-level paid levers** (ROAS by campaign, channel CVR) as low-confidence — but this does **not** block the Shopify-sourced funnel brief. Spend-side levers (budget allocation, frequency, demo mix) stay reliable; precise paid-attribution dollars do not.

Record both checks in evidence. Most accounts have broken attribution and clean Shopify — so most accounts can still get a full exact funnel brief; only the paid-channel specifics get caveated.

3. **Denominator integrity.** If `orders ÷ sessions` is implausibly low for the AOV tier, the site carries non-shopping traffic (software / community / app). Suppress the sessions-CVR lever; use the Shopify checkout funnel (`orders ÷ (orders + abandoned_checkouts)`) as the conversion measure and note the cause in evidence + memory. (Live example: a VR hardware brand whose software-download traffic made sessions-CVR 0.045% — a denominator artifact, not a conversion problem.)

## Step 2 — Score
```bash
python3 scripts/score.py --values clients/{Client}/funnel/{date}/node-values.csv --baseline {monthly_rev} --ret-baseline {returning_rev} --cm2 {CM2} --out clients/{Client}/funnel/{date}/levers.json
```
Emits ranked levers (revenue + profit), each labelled `exact` or `prior`, with its dollar figures, confidence, and graph-derived causal chain. `--ret-baseline` enables exact math for retention factors.

## Step 2.5 — Generate plays
For the top levers, read the lever's owning chunk + the live inventory and write `clients/{Client}/funnel/{date}/plays.json` per `references/play-generation.md`. Each play names only real entities and carries its `target → intermediate → outcome — why` chain (reuse the lever's chain from `levers.json`).

## Step 3 — VERIFY (the gate)
```bash
python3 scripts/verify.py --values clients/{Client}/funnel/{date}/node-values.csv --levers clients/{Client}/funnel/{date}/levers.json --plays clients/{Client}/funnel/{date}/plays.json --inventory clients/{Client}/funnel/{date}/inventory.csv
```
**If this exits non-zero, do NOT build the report.** Read the violations, fix the offending value/play/chain, re-run. Only proceed on exit 0.

## Step 4 — Build the report
First write `clients/{Client}/funnel/{date}/flags.json` — a JSON list of the **fixes/connections** that would unlock more levers, each `{area, status (broken|warning|info), off, missing, fix}`: broken/partial tracking (CAPI/GA4 gap, GA4 sync-lag, failed funnel queries) and sources connected-but-not-pulled or not-connected (e.g. Klaviyo, reviews app). Each flag is counted in the banner as a "thing to fix to measure more." Also pass `--target` = the account's realistic measurable-lever count (from its coverage map; e.g. ~40), so coverage reads against an achievable target, not all 88. Then:
```bash
python3 scripts/build_report.py --levers clients/{Client}/funnel/{date}/levers.json --plays clients/{Client}/funnel/{date}/plays.json --flags clients/{Client}/funnel/{date}/flags.json --target {N} --baseline-source "{Shopify|GA4|Triple Whale}" --client "{Client}" --out clients/{Client}/funnel/{date}/report.html
```
Self-contained HTML gap brief (see `references/output-spec.md`): light theme. The top banner **leads with "N fixes/connections would unlock more levers"** (so partial coverage reads as an action list, not under-reporting) and frames measured against the realistic `--target`. When `--baseline-source` is not a financial source of truth, a **"Directional dollars" notice** appears so a GA4-undercounted number never reads as exact. Then the answer, heat strip, opportunity ladder, and per-lever drawers.

## Step 5 — Present + learn-as-you-go + handoff
In chat, state the result and **teach the chain in plain words**: "The biggest profit lever is cross-sell attach — raising it lifts AOV, and AOV is a direct multiplier of revenue, so a 5%→15% move is ~$20k/mo at your margin." Then route the top lever to its arm (paid → `/ads`; else the chunk). End with ONE concrete next action.

## Step 6 — Memory
Append a dated one-liner under `## Recurring Patterns` in `clients/{Client}/CLAUDE.md`: top revenue lever + top profit lever this run. Append-only; never touch Identity/Brand/Standing Context.

## Step 6.5 — Log predictions (per-account self-calibration)
Append one `open` row per recommended lever to `clients/{Client}/outcomes-log.csv` (date, lever, method, predicted_rev/profit, target, metric_before). At 30/60/90 days, fill the actuals and set `status=closed`, then run `python3 scripts/calibrate.py --log clients/{Client}/outcomes-log.csv` to get per-account **prior strength multipliers** and **exact attainment factors**. This is the real calibration loop — each account corrects itself over time; no cross-account pooling. See `references/calibration.md`.

## Step 7 — Capture skill learnings (append-only; never self-edit the skill)
If, during the run, you hit a data gap, a flaky metric key, a benchmark that didn't fit, or any methodology limitation, append ONE dated line to a `funnel-skill-learnings.md` file at your workspace root (not shipped in the package). Format: `- {date} ({client}): {what happened} → {proposed skill change}`. This is the only "self-improvement" the skill does automatically — it **records** learnings, it does **not** edit its own source or repackage. Promotion to an actual skill change is deliberate and human-gated: when the same learning appears ~3 times (or the user asks to update the skill from learnings), edit the skill source deliberately. Do NOT rewrite/repackage the skill mid-run.

## Reference files
- `references/grounding-rules.md` — the anti-hallucination contract (enforced by verify.py).
- `references/calibration.md` — three-tier calibration (exact identity / per-account prior / outcome loop); why no cross-account pooling is needed.
- `references/output-spec.md` — exact report layout + why-chain format.
- `references/play-generation.md` — how to write grounded plays from live inventory.
- `references/node-metric-map.md` — node → MCP source + direction-of-good.
- `references/data-layer.md` — MCP pull patterns + values/inventory schemas.
- `references/scoring-methodology.md` — Headroom × Sensitivity, revenue vs profit, long-run.
- `references/handoff.md` — lever → execution-arm routing.
- `references/benchmarks.md` — benchmark ceilings by AOV tier (defer to your own vertical benchmark library if you maintain one).
- `references/funnel-nodes.csv`, `references/funnel-edges.csv` — the verified 88-node graph (data model).
- Sample data: `sample-node-values.csv`, `sample-inventory.csv`, `sample-plays.json` — make the pipeline runnable before live data.

## Scripts
- `scripts/score.py` — sensitivity + dollars + causal chains → `levers.json`.
- `scripts/verify.py` — the hallucination gate (provenance, dollars, chains, entities). Run before every report.
- `scripts/build_report.py` — renders the HTML gap brief from verified inputs.
- `scripts/calibrate.py` — reads the outcomes log → per-account prior multipliers + exact attainment factors.

## Relationship to the system
Data model & diagnosis are owned by `references/funnel-decomposition.md` and `references/funnel-diagnostic.md`; thresholds by `benchmarks.md`; paid execution by `/ads`. This skill decides *where the biggest lever is* and *why*, then points the right arm at it.
