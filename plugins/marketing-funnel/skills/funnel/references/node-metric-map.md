# Node → Metric Map

For each funnel node: where to pull its current value, which direction is "good," and the benchmark anchor. `score.py` needs `current`, `benchmark`, and `higher_is_better` per measured node. Nodes marked **(derive)** are computed from other pulls; **(qual)** have no clean numeric pull — estimate or skip and flag in coverage.

**Shopify-derived shortcuts (robust, no GA4 needed — preferred for the EXACT levers):**
- `checkout` (completion) = `Shopify@orders ÷ (Shopify@orders + Shopify@aband_checkouts)`
- `cart_aband` = `Shopify@aband_checkouts ÷ (Shopify@orders + Shopify@aband_checkouts)`
- `aov` = `Shopify@totalsales ÷ Shopify@orders` · `return_rate` = `|Shopify@refunds| ÷ Shopify@totalsales`

**Video metrics — hook / hold / watch (compute cleanly, never ÷ total impressions):**
The naive hook rate (`3-sec views ÷ all impressions`) is wrong because the denominator includes static-ad impressions that can never produce a video view — it understates the true rate. Compute these from **video-only** denominators via the **Meta Ads MCP** (`ads_get_ad_entities`), and prefer pulling at **ad level**, summing only over ads that report video metrics (`video_p25_watched_actions > 0`), so static ads never enter the denominator:
- `hook` = `video_continuous_2_sec_watched_actions ÷ impressions[video ads]`. Meta deprecated 3-sec views; **2-sec-continuous is the current hook signal**. If it returns `Not available` for the account, fall back to `video_p25_watched_actions ÷ impressions[video ads]` (25%-watched as the started-watching proxy) and mark `hook` confidence MEDIUM.
- `hold` = `video_thruplay_watched_actions ÷ impressions[video ads]` (ThruPlay rate). For a "of those who started" read, use `thruplay ÷ video_p25_watched_actions`.
- `watch` = completion/retention from the curve: `video_p100_watched_actions ÷ video_p25_watched_actions` (% who finish of those who started). Meta does **not** expose avg-watch-seconds via the MCP — use the p25→p50→p75→p100 curve, not a seconds value.
- **Verified field names** (`ads_get_field_context`, 2026-06): `video_continuous_2_sec_watched_actions`, `video_thruplay_watched_actions`, `video_p25/p50/p75/p100_watched_actions`, `impressions`. NOT available: `video_3_sec_watched_actions`, `video_play_actions`, `video_avg_time_watched_actions`.
- **Databox-only fallback (account not on the Meta MCP):** Databox `FbAds@video_view` gives 3-sec views but there is **no** video-impressions, ThruPlay, or avg-watch metric — so a *clean* hook is not computable and hold/watch are unavailable. In that case report `hook` as a **diluted video-view rate** (`FbAds@video_view ÷ FbAds@impressions`), tag it LOW confidence, and raise a data-completeness fix: "enable this account's Meta ad account on the Meta Ads MCP, or publish video-plays / ThruPlay / avg-watch-time as Databox custom metrics." Leave `hold`/`watch` as `DATA_NOT_AVAILABLE`.

**Benchmark video levers against the account's OWN best ad, not an industry number.** The industry "hook 25%" anchor assumes 3-sec views; when only p25 (25%-watched) is available the two aren't comparable, and scoring p25 against a 3-sec benchmark is wrong. Instead set the benchmark for `hook`/`hold`/`watch` to the account's **best-performing video ad** for that metric (from the ad-level pull). This is more honest ("you already hit 46.7% on one ad, you average 11.3%") and more actionable than a generic ceiling.

**Per-ad misallocation is usually the real lever (compute it, don't eyeball it).** The account-level hook average hides the money. Build the ad-level table (impressions, hook, hold per video ad) and look for **high-delivery / low-hook** ads: budget concentrated on a weak-hook creative while a proven high-hook ad is starved. That delivery×hook mismatch is the lever — generate it as the primary play for the `hook` node (reallocate spend toward proven scroll-stoppers; no new creative, no added spend). Live example (outdoor-furniture brand, May 2026): one video ad took ~48% of video delivery at a 2.8% hook while another hooked 46.7%.

**Denominator warning for `cvr` / sessions-based rates:** never use raw GA4 sessions as the conversion denominator when the site has non-shopping traffic (software/community/app). Use the Shopify checkout funnel instead and flag sessions as polluted (see grounding-rules.md).

Sources: DBX = Databox, TW = Triple Whale (moby), GA4, KLV = Klaviyo, META = Meta Ads MCP, SW = SimilarWeb/Ahrefs (optional).

## Identity spine & output
| id | label | source | example metric | good dir |
|---|---|---|---|---|
| revenue | REVENUE | TW / DBX (Shopify) | total_revenue | higher |
| orders | Orders | TW / Shopify | orders | higher |
| sessions | Sessions | GA4 | sessions | higher |
| cvr_id / cvr | Sitewide CVR | GA4 / Shopify | conversion_rate | higher |
| aov | AOV | TW / Shopify | average_order_value | higher |
| ret_rev | Returning revenue | TW | returning_customer_revenue | higher |

## TOF — demand creation
| id | label | source | metric | good dir |
|---|---|---|---|---|
| tof_spend | Prospecting spend | DBX/META | spend (prospecting) | context |
| impressions | Impressions | DBX/META | impressions | higher |
| reach | Reach | META | reach | higher |
| frequency | Frequency | META | frequency | lower |
| cpm | CPM | DBX/META | cpm | lower |
| pct_new | % new reach | META | % new audience | higher |
| cre_vol | Creative volume | META | # active ads (distinct) | higher |
| cre_div | Creative diversity | META (qual) | Andromeda diversity | higher |
| hook | Hook rate | META (derive) | 2-sec-cont ÷ video impr (see Video block) | higher |
| hold | Hold rate | META (derive) | ThruPlays ÷ video impr (see Video block) | higher |
| watch | Watch completion | META (derive) | p100 ÷ p25 (see Video block) | higher |
| ctr | Ad CTR | DBX/META | ctr | higher |
| cpc | CPC | DBX/META | cpc | lower |
| lpv_rate | LP-view rate | META | lpv / link_clicks | higher |
| nvs | New-visitor sessions | GA4 | new_users sessions | higher |
| organic | Organic sessions | GA4 | organic_sessions | higher |
| brand | Branded search | GA4/GSC/SW | branded_search_clicks | higher |
| direct | Direct traffic | GA4 | direct_sessions | higher |
| referral | Referral traffic | GA4 | referral_sessions | higher |
| follow | Follower growth | DBX (social) | net_follower_growth | higher |
| sov | Share of voice | SW/Ahrefs (qual) | share_of_voice | higher |
| ugc_reach | UGC / influencer reach | DBX/manual (qual) | creator_reach | higher |

## MOF — capture & nurture
| id | label | source | metric | good dir |
|---|---|---|---|---|
| lpv | Landing page views | GA4 | landing_page_views | higher |
| bounce | Bounce rate | GA4 | bounce_rate | lower |
| eng_rate | Engagement rate | GA4 | engagement_rate | higher |
| pages_sess | Pages / session | GA4 | pages_per_session | higher |
| eng_time | Avg engaged time | GA4 | avg_engagement_time | higher |
| pdp_views | Product page views | GA4 | view_item events | higher |
| pdp_rate | PDP view rate | GA4 (derive) | view_item / sessions | higher |
| atc_rate | Add-to-cart rate | GA4 | add_to_cart / view_item | higher |
| atc_vol | Add-to-cart volume | GA4 | add_to_cart events | higher |
| email_cap | Email capture rate | KLV/GA4 (derive) | new_subs / sessions | higher |
| sms_cap | SMS opt-in rate | KLV (derive) | sms_subs / sessions | higher |
| quiz | Quiz completion | GA4/app | quiz_complete | higher |
| lead_mag | Lead-magnet uptake | KLV/GA4 | lead_form_submits | higher |
| list_growth | List growth rate | KLV | net_new_subscribers | higher |
| list_size | List size | KLV | active_profiles | higher |
| deliver | Deliverability | KLV | inbox_placement / bounce | higher |
| open_rate | Email open rate | KLV | open_rate | higher |
| click_rate | Email click rate | KLV | click_rate | higher |
| flow_ctr | Flow click rate | KLV | flow_click_rate | higher |
| rvr | Returning-visitor rate | GA4 | returning / total sessions | higher |
| rtg_pool | Retargeting pool | META | warm_audience_size | higher |
| bis | Back-in-stock / wishlist | app/KLV | bis_signups | higher |

## BOF — conversion
| id | label | source | metric | good dir |
|---|---|---|---|---|
| ic_rate | Initiate-checkout rate | GA4 | begin_checkout / add_to_cart | higher |
| checkout | Checkout completion | GA4/Shopify | purchase / begin_checkout | higher |
| cart_aband | Cart abandonment | GA4/Shopify | 1 − ic_rate | lower |
| co_aband | Checkout abandonment | GA4/Shopify | 1 − checkout | lower |
| new_cvr | New-visitor CVR | GA4 | cvr (new users) | higher |
| ret_cvr | Returning-visitor CVR | GA4 | cvr (returning) | higher |
| mob_cvr | Mobile CVR | GA4 | cvr (mobile) | higher |
| rtcvr | Retarget/branded CVR | GA4/DBX | cvr (retargeting+branded) | higher |
| pay_success | Payment success rate | Shopify | authorized / attempted | higher |
| site_speed | Site speed (LCP) | GA4/PSI | lcp (inverted) | higher |
| trust | Trust / review rating | reviews app (qual) | avg_review_rating | higher |
| express_co | Express checkout rate | Shopify | shop_pay / total checkouts | higher |

## AOV — offer mechanics
| id | source | metric | good dir |
|---|---|---|---|
| upo | TW/Shopify | units_per_order | higher |
| asp | TW/Shopify | avg_selling_price | context |
| attach | Shopify | cross_sell_attach_rate | higher |
| upsell | upsell app | upsell_take_rate | higher |
| bundle | Shopify | bundle_order_share | higher |
| sub_attach | sub app | subscription_attach_rate | higher |
| ship_gap | Shopify (derive) | gap_to_free_ship | lower |
| bnpl | Shopify | bnpl_share | higher |
| discount | Shopify | discount_rate | context |
| gwp | Shopify | gwp_uptake | higher |

## Retention — LTV loop
| id | source | metric | good dir |
|---|---|---|---|
| repeat_rate | TW | repeat_purchase_rate | higher |
| freq | TW | purchase_frequency | higher |
| ibt | TW | days_between_orders | lower |
| ltv | TW | ltv_60/90d | higher |
| rep_30_90 | TW | 30/60/90d repeat | higher |
| sub_active | sub app | active_subscriptions | higher |
| sub_churn | sub app | subscription_churn | lower |
| winback | KLV | winback_revenue/rate | higher |
| pp_flow_rev | KLV | post_purchase_flow_revenue | higher |
| loyalty | loyalty app | active_members | higher |
| referral_rate | referral app | referral_rate | higher |
| review_rate | reviews app | review_submission_rate | higher |
| return_rate | Shopify | return_rate | lower |
| replenish | TW (derive) | replenishment_rate | higher |
| nps | survey (qual) | nps | higher |

**Direction note:** `good dir = lower` nodes are the negative drivers in the graph (cart_aband, co_aband, bounce, frequency, cpm, cpc, ibt, sub_churn, return_rate, ship_gap). For these, "headroom to improve" = how far CURRENT is ABOVE the benchmark (room to bring it down). `score.py` handles this via the `higher_is_better` flag.
