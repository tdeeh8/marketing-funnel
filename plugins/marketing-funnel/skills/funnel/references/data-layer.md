# Data Layer — MCP pull patterns

**Allowed sources: Databox MCP + Meta Ads MCP only.** Everything below resolves through one of these two.

Pull each mapped node's CURRENT value (trailing 28–30 days unless the user asks otherwise) and its prior-period value if available (for trend context). Cite every value's source. Save raw responses to `clients/{Client}/funnel/{date}/evidence/`. Never invent a number — null → `DATA_NOT_AVAILABLE`.

## Source of truth & the selective gate (read first)
The funnel/identity layer and the channel-attribution layer come from different sources and fail independently:

- **Funnel / financial truth → Shopify** (or BigCommerce), via the Databox Shopify connector: revenue, orders, AOV, sitewide CVR (orders ÷ sessions), checkout completion, cart abandonment, units-per-order. **Reliable even when paid attribution is broken.** This is what powers the EXACT levers. Source priority: Shopify > GA4.
- **On-site behavior → GA4**: sessions, bounce, engagement, PDP views, add-to-cart, begin-checkout (for the on-site rates). Use as a denominator/behavioral source, not for revenue.
- **Channel attribution → GA4 / CAPI / platform**: ROAS by channel/campaign, channel-level CVR. This is the layer that breaks on most accounts. When paid coverage <70% or CAPI is >15% off Shopify, mark these channel-level paid levers low-confidence — but the Shopify funnel brief still runs.

Practical implication: a missing or broken paid pixel does NOT stop the exact funnel prioritization, as long as Shopify is connected. If Shopify is NOT connected (e.g., it's absent from Databox), that is the real blocker — connect it (Databox Shopify connector) and the full brief runs.

## Databox (paid + cross-channel)
1. `list_metrics` to discover available metric keys for the connected data sources (Meta, Google, Shopify, GA4 if piped through Databox).
2. `load_metric_data` for each needed key over the window. Record the `metric_key` as the citation.
- Best for: spend, impressions, reach, CPM, CTR, CPC, channel revenue/ROAS, follower growth.
- The `/ads` skill's `references/data-layer/databox-data-layer.md` has the account-cache + key-discovery flow — reuse it; don't reinvent.

**Backfill granulation hard rule:** Databox weekly and monthly granulation returns WRONG numbers. In backfill mode (and any time you need a value for a specific historical week), always make **one whole-range call per metric per week window** — pass the explicit start and end date of that week as the pull range. Never use `granularity=weekly` or `granularity=monthly` to derive historical week-by-week values; the numbers are unreliable.

## GA4
- Behavioral funnel: sessions (by source/medium → new/organic/direct/referral), bounce/engagement rate, pages per session, engaged time, `view_item`, `add_to_cart`, `begin_checkout`, `purchase` (for PDP rate, ATC rate, IC rate, checkout completion), mobile vs desktop CVR.
- GA4 under-counts revenue (use Shopify for $); use GA4 for RATES and behavior, not for the revenue denominator.

## Klaviyo (via Databox connector only)
Email/SMS metrics come through the account's Databox Klaviyo connector. If Klaviyo is not connected in Databox, these nodes are DATA_NOT_AVAILABLE — flag it; do NOT pull a direct Klaviyo MCP.
- List size (active profiles), net new subscribers (list growth), open/click rates, flow click rate, post-purchase flow revenue, deliverability/inbox placement, winback.

## Meta Ads MCP — CHECK THIS FIRST for Meta (before Databox FbAds)
When running a client, resolve the Meta data via the **Meta Ads MCP first**, and only fall back to Databox `FbAds@*` if the account isn't reachable there. The Meta Ads MCP exposes levers Databox does **not**: thruplay/hold, avg watch time, %-new-audience, distinct active-creative count (cre_vol / Andromeda diversity), and warm/retargeting-pool size — plus frequency, CTR, CPM, CPC.
- Flow: `ads_get_ad_accounts` → match the client's account by name (confirm `is_ads_mcp_enabled`) → `ads_insights_performance_trend` / entity pulls for frequency, CTR, CPM, CPC, reach; entity pulls for hook/hold/watch/cre_vol.
- **Verify availability LIVE every run — never trust a cached config note.** Client configs (`audit-config.json` / `playbook-config.json` / client CLAUDE.md) may say "not on the Meta MCP," but access changes as accounts get added and Meta's rollout expands. Run `ads_get_ad_accounts` each run and match by `ad_account_name` / `business_name`; if a candidate account has an empty name, probe it with a campaign-level `ads_get_ad_entities` pull and match campaign names against the client's known campaign inventory before concluding. Then **update the client config note with the dated check result** (connected or not) so the record never goes stale. If still unavailable, fall back to Databox FbAds and keep the "enable Meta MCP" data-completeness flag, citing the check date in the flag's `off` text.
- **Clean hook/hold/watch (video-only, never ÷ total impressions).** Pull via `ads_get_ad_entities` at **ad level** with fields `["impressions","video_continuous_2_sec_watched_actions","video_thruplay_watched_actions","video_p25_watched_actions","video_p100_watched_actions"]`, then sum over only the ads that report video (p25 > 0) so static-ad impressions never pollute the denominator:
  - `hook` = Σ 2-sec-continuous ÷ Σ video impressions (fallback Σ p25 ÷ Σ video impr if 2-sec = "Not available" — varies by account; some accounts lack the 2-sec signal or are not on the Meta MCP).
  - `hold` = Σ ThruPlays ÷ Σ video impressions. `watch` = Σ p100 ÷ Σ p25 (completion; no avg-seconds via MCP).
  - Verified field names + the per-account-availability caveat live in `node-metric-map.md` → "Video metrics" block. Cite the field name as the source.
- Databox `FbAds@*` remains the fallback for the basics (spend, frequency, cpm, ctr) when the Meta MCP account isn't accessible. Note Databox FbAds exposes only `FbAds@video_view` (3-sec views) + `FbAds@impressions` — enough for a **diluted** hook only; hold/watch are not in Databox. For Databox-only accounts, report hook LOW-confidence and flag "enable Meta MCP for this account" as the fix.

## Mapping to the values file (provenance required)
After pulls, write `clients/{Client}/funnel/{date}/node-values.csv` with one row per node — and a `source` + `window` for every measured value (the grounding gate fails without them):

```
id,current,benchmark,higher_is_better,measured,source,window,incr_spend
cvr,0.021,0.030,1,1,ga4:conversion_rate,2026-05,
cart_aband,0.78,0.68,0,1,shopify:cart_abandonment,2026-05,
list_growth,420,900,1,1,klaviyo:net_new_subscribers,2026-05,
reach,500000,800000,1,1,meta:reach_prospecting,2026-05,20000
...
```

- `source` = the exact MCP metric key / entity id the value came from. Required for measured rows.
- `window` = the date range pulled (e.g. `2026-05` or `2026-05-01..2026-05-30`).
- `incr_spend` = optional; for PAID levers, the incremental media spend a play would add — needed to compute profit (left blank → paid-lever profit shows `—`, never faked).
- `benchmark` from `references/benchmarks.md` (by AOV tier). `higher_is_better` = 1 for normal levers, 0 for negative drivers.
- `measured` = 1 if a real value was pulled; 0 (or `DATA_NOT_AVAILABLE`) otherwise — excluded from scoring, counted in coverage.

## Inventory pull (grounds the plays)
For the top levers' domains, also pull live entities → `clients/{Client}/funnel/{date}/inventory.csv` (`entity_id,type,name,attrs`):
- Meta/Google campaigns (name, active creatives, frequency, audience, status).
- Klaviyo flows (name + on/off/missing).
- Shopify offers (bundles live, upsell app, subscription, free-ship threshold).

Plays may only name entities that appear here — `verify.py` rejects any play that references a campaign/flow/offer not in this file.

## Field-tested notes (from live runs)
- **Read the client config for IDs.** `clients/{Client}/playbook-config.json` (or `audit-config.json`) holds `databox_account_id` and per-platform `*_data_source_id` (Shopify, GA4, Google, Meta) plus AOV tier, CM2, target CAC. Read it in Step 0 — it's how you address the right data sources without guessing.
- **Shopify-derive checkout completion (no GA4 needed).** `checkout = orders ÷ (orders + Shopify@aband_checkouts)`; cart abandonment = the complement. `AOV = Shopify@totalsales ÷ Shopify@orders`. `return_rate = |Shopify@refunds| ÷ Shopify@totalsales`. These are the most robust EXACT levers and survive broken GA4/CAPI entirely.
- **Funnel fallback chain** for PDP→ATC→checkout rates: GA4 custom funnel queries first; if they error (they can 500 / auth-fail per space), fall back to GA4 standard events; else use the Shopify-derived checkout above and mark the deeper rates `DATA_NOT_AVAILABLE`.
- **Polluted-sessions guard (critical).** Do NOT compute a sessions-based CVR when the site carries large non-shopping traffic (software, community, support, app). Tell: `orders ÷ sessions` is wildly below the AOV-tier benchmark (live example: a software-download site showed 0.045%). When you see this, suppress the sessions-CVR lever, use the Shopify checkout funnel as the denominator, and note the cause (e.g. "non-shopping software traffic") in evidence + client memory.
- **Databox MCP quirks.** Custom-query metric keys (`{id}|custom_query_…`) are flaky via the MCP — the `metric_name` argument is required on some spaces and rejected on others, and they can 500 / auth-fail. Don't depend on them; if they fail, use the Shopify-derived checkout funnel. Some calls time out — retry once. Pull the robust delivery metrics (spend, frequency, CPM, CTR) for the paid layer; treat ROAS / attributed-purchases as low-confidence when CAPI/GA4 coverage is poor.
- **Always pull GA4 behavioral.** `engagementRate`, `averageSessionDuration` (avg engaged time), `bounceRate`, `screenPageViewsPerSession` add MOF levers (eng_rate, eng_time, bounce, pages_sess) and survive broken conversion attribution — pull them every run, not just when convenient.
- **Partial-window guard (GA4 sync lag).** GA4 in Databox often lags ~7–10 days. Check each returned data point's `end_timestamp`; if it falls short of the requested `end_date`, the value covers a partial window — append `-partial` to its `window`, treat it as low-confidence, and surface it in the report's data-completeness banner.
- **Baseline source dictates whether dollars are exact or directional.** When the revenue baseline comes from Shopify, the dollar figures are exact-grade. When it comes from **GA4** (no ecommerce platform connected), GA4 under-counts (often badly — live example: an account at 28.6% paid coverage), so EVERY dollar is directional. Pass `--baseline-source "GA4"` (or `"Shopify"`) to `build_report.py`; a non-financial source flips on a visible "Directional dollars" notice so an undercounted number never reads as an exact forecast.
- **Google Ads CPC key varies — discover it.** `GoogleAds@cpc` has returned empty on some accounts. Don't assume the key; run `list_metrics` on the Google Ads data source and match the CPC metric, or skip CPC and mark `DATA_NOT_AVAILABLE` rather than guessing.
- **Returns hit gross revenue directly.** The graph now has `return_rate → revenue` (negative) in addition to the retention paths, so high-return / mostly-one-time-buyer accounts rank returns by their real top-line cost, not just the small retention slice. Live example: an account with 91% new-customer mix and 16% return rate had returns as one of its top revenue levers.
