# Funnel Diagnostic Playbook

Last updated: 2026-06-02. Sources: funnel-decomposition.md (the tree), benchmarks.md (thresholds), measurement.md (tracking), and the verified funnel correlation graph (funnel-nodes.csv / funnel-edges.csv). Status: DIAGNOSTIC PROCEDURE — turns the lever graph into a repeatable "something is off → what do I pull?" routine. It routes to fixes; it does not restate channel tactics.

> **What this is.** The correlation graph is the engine; this is the operating manual. Every node is verified to trace upstream to exogenous levers and downstream to revenue, so the diagnosis always terminates in a knob you can turn. The per-node reference below is GENERATED from the graph — it cannot drift from the data model.

## The method — 5 steps

1. **Name the symptom and confirm it is real.** Pick the single metric that is off versus its benchmark (benchmarks.md). Before anything else, rule out a tracking break (measurement.md) — broken tracking mimics a performance drop perfectly.
2. **Localize on the identity spine (deterministic).** Revenue off? → is it **Orders** or **AOV**? Orders → **Sessions** or **CVR**? This isolates the branch with math, zero guessing. (funnel-decomposition.md owns the tree.)
3. **Walk upstream by strength.** From the broken metric, follow its inbound edges to the drivers, **strongest first**. Watch the **sign**: a *negative* driver is the culprit when it is **HIGH** (cart abandonment up → CVR down). Watch the **lag**: long-lag drivers were set in motion weeks ago, so today's symptom may trace to a TOF decision from a month back.
4. **Reach the input lever.** Keep walking upstream until you hit an exogenous lever (a knob you control). Those are your levers to pull — listed per node below as "root inputs."
5. **Apply the fix from the owning chunk, then watch the leading indicator — not revenue.** Fix tactics live in the channel chunks (see routing). After acting, track the upstream leading indicator and respect the lag before judging.

## Reading rules

- **Identity vs signal.** Spine edges are deterministic — trust them immediately. Signal edges (everything else) are hypothesized strengths; on a single account, treat a weak edge as a lead, not proof, until cross-account validation fills the real coefficient (funnel-decomposition.md).
- **Strength = priority, not certainty.** Rank candidate causes by edge strength, but verify before betting budget.
- **Negative driver high = the problem.** When a node's causes include a negative driver, check whether that driver is elevated.
- **Mind the lag.** A flat symptom today with a lagged upstream cause means the damage is already weeks deep — and the fix will take weeks to show.

## Per-node root-cause reference (generated from the verified graph)

For any metric that's off: read its **direct causes** (ranked), trace to the **levers to pull**, and fix via the routed chunk.

### Revenue
**REVENUE** — _Total revenue (source of truth)._
  - Direct causes (strongest first): Orders (+1.0), AOV (+0.95), Returning revenue (+0.7), List size (+0.45, ~1wk), Email click rate (+0.4, ~2wk), Post-purchase flow revenue (+0.4, ~2wk)
  - Levers to pull (root inputs): Cart abandonment (0.61), Organic sessions (0.54), Upsell take rate (0.52), Checkout abandonment (0.49), New-visitor CVR (0.49), Mobile CVR (0.49)
  - Fix via: CRO + measurement.md (tracking) + low-ticket.md (friction); tof-strategy.md (branded search → measurement.md); low-ticket.md (AOV) + high-ticket.md (BNPL) + post-purchase.md (upsell)

### Spine
**Returning revenue** — _Returning orders x AOV._
  - Direct causes (strongest first): Repeat purchase rate (+0.7), Customer LTV (+0.7), Purchase frequency (+0.6), Active subscriptions (+0.6), Post-purchase flow revenue (+0.6, ~2wk), Reactivation rate (+0.4, ~2wk), Return / refund rate (−0.4)
  - Levers to pull (root inputs): 30/60/90-day repeat (0.42), Reactivation rate (0.40), Return / refund rate (0.40), Subscription churn (0.36), Time between orders (0.36), Loyalty participation (0.35)
  - Fix via: post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Return / refund rate
**Sessions** — _Total visits = sum of all sources._
  - Direct causes (strongest first): Branded search (+0.72, ~5wk), New-visitor sessions (+0.7, ~1wk), Organic sessions (+0.6), Direct traffic (+0.6, ~5wk), Returning-visitor rate (+0.45, ~1wk), Referral traffic (+0.4)
  - Levers to pull (root inputs): Organic sessions (0.60), % new reach (0.35), UGC / influencer reach (0.29), Follower growth (0.29), CPM (0.21), Review submission rate (0.14)
  - Fix via: tof-strategy.md (branded search → measurement.md); tof-strategy.md / scaling-frequency.md; post-purchase.md + email-sms.md
**Orders** — _Sessions x CVR._
  - Direct causes (strongest first): Sessions (+0.9), CVR (identity) (+0.9), Add-to-cart volume (+0.4)
  - Levers to pull (root inputs): Cart abandonment (0.61), Organic sessions (0.54), Checkout abandonment (0.49), New-visitor CVR (0.49), Mobile CVR (0.49), Site speed (LCP) (0.45)
  - Fix via: CRO + measurement.md (tracking) + low-ticket.md (friction); tof-strategy.md (branded search → measurement.md)
**CVR (identity)** — _Conversion multiplier._
  - Direct causes (strongest first): Sitewide CVR (+0.9)
  - Levers to pull (root inputs): Cart abandonment (0.68), Checkout abandonment (0.54), New-visitor CVR (0.54), Mobile CVR (0.54), Site speed (LCP) (0.50), PDP view rate (0.45)
  - Fix via: CRO + measurement.md (tracking) + low-ticket.md (friction); site CRO (low-ticket.md / high-ticket.md landing & PDP sections)

### BOF
**Sitewide CVR** — _Sessions to orders._
  - Direct causes (strongest first): Checkout completion (+0.8), Cart abandonment (−0.75), Checkout abandonment (−0.6), New-visitor CVR (+0.6), Returning-visitor CVR (+0.6), Mobile CVR (+0.6), Initiate-checkout rate (+0.55), Retarget / branded CVR (+0.55), Site speed (LCP) (+0.55), Trust / review rating (+0.5), PDP view rate (+0.5), Add-to-cart rate (+0.5), Bounce rate (−0.5), Avg engaged time (+0.45), Pages per session (+0.4), Engagement rate (+0.4), Discount depth (+0.4), Back-in-stock / wishlist (+0.3, ~2wk)
  - Levers to pull (root inputs): Cart abandonment (0.75), Checkout abandonment (0.60), New-visitor CVR (0.60), Mobile CVR (0.60), Site speed (LCP) (0.55), PDP view rate (0.50)
  - Fix via: CRO + measurement.md (tracking) + low-ticket.md (friction); site CRO (low-ticket.md / high-ticket.md landing & PDP sections)
  - ⚠ Culprit-when-high (negative drivers): Cart abandonment, Checkout abandonment, Bounce rate
**Checkout completion** — _Checkout start to purchase._
  - Direct causes (strongest first): Payment success rate (+0.6), Checkout abandonment (−0.6), Express checkout rate (+0.45)
  - Levers to pull (root inputs): Payment success rate (0.60), Checkout abandonment (0.60), Express checkout rate (0.45)
  - Fix via: CRO + measurement.md (tracking) + low-ticket.md (friction)
  - ⚠ Culprit-when-high (negative drivers): Checkout abandonment
**Initiate-checkout rate** — _ATC to checkout start._
  - Direct causes (strongest first): Add-to-cart rate (+0.7)
  - Levers to pull (root inputs): Add-to-cart rate (0.70)
  - Fix via: site CRO (low-ticket.md / high-ticket.md landing & PDP sections)
**Returning-visitor CVR** — _Conversion of return visitors._
  - Direct causes (strongest first): Returning-visitor rate (+0.5, ~1wk)
  - Levers to pull (root inputs): Deliverability (0.09), CPM (0.06), UGC / influencer reach (0.06), PDP view rate (0.04), Return / refund rate (0.02), % new reach (0.02)
  - Fix via: email-sms.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); site CRO (low-ticket.md / high-ticket.md landing & PDP sections); post-purchase.md + email-sms.md
**Retarget / branded CVR** — _Conversion of warm traffic._
  - Direct causes (strongest first): Retargeting pool (+0.6, ~1wk)
  - Levers to pull (root inputs): CPM (0.18), UGC / influencer reach (0.18), PDP view rate (0.12), Return / refund rate (0.06), % new reach (0.05), Time between orders (0.05)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); site CRO (low-ticket.md / high-ticket.md landing & PDP sections); post-purchase.md + email-sms.md
**Trust / review rating** — _Social proof & credibility on-site._
  - Direct causes (strongest first): Review submission rate (+0.5, ~2wk)
  - Levers to pull (root inputs): Review submission rate (0.50)
  - Fix via: post-purchase.md + email-sms.md

### MOF
**List growth rate** — _Net new subscribers / week (KEYSTONE)._
  - Direct causes (strongest first): Email capture rate (+0.7, ~1wk), SMS opt-in rate (+0.6, ~1wk), New-visitor sessions (+0.55, ~1wk)
  - Levers to pull (root inputs): SMS opt-in rate (0.60), Quiz completion (0.35), Lead-magnet uptake (0.35), % new reach (0.28), CPM (0.17), UGC / influencer reach (0.17)
  - Fix via: list-building.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md)
**Landing page views** — _Sessions that load a landing/entry page._
  - Direct causes (strongest first): New-visitor sessions (+0.7), Landing-page-view rate (+0.6)
  - Levers to pull (root inputs): % new reach (0.35), CPM (0.21), UGC / influencer reach (0.21), Return / refund rate (0.07), Time between orders (0.05), 30/60/90-day repeat (0.05)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
**Product page views** — _PDP load count._
  - Direct causes (strongest first): Landing page views (+0.6), PDP view rate (+0.5)
  - Levers to pull (root inputs): PDP view rate (0.50), % new reach (0.21), CPM (0.13), UGC / influencer reach (0.13), Return / refund rate (0.04), Time between orders (0.03)
  - Fix via: site CRO (low-ticket.md / high-ticket.md landing & PDP sections); tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
**Email capture rate** — _Sessions converted to email subscriber._
  - Direct causes (strongest first): Quiz completion (+0.5), Lead-magnet uptake (+0.5)
  - Levers to pull (root inputs): Quiz completion (0.50), Lead-magnet uptake (0.50)
  - Fix via: list-building.md
**Returning-visitor rate** — _Share of sessions that are returns._
  - Direct causes (strongest first): Email click rate (+0.5, ~1wk), Retargeting pool (+0.4, ~1wk)
  - Levers to pull (root inputs): Deliverability (0.18), CPM (0.12), UGC / influencer reach (0.12), PDP view rate (0.08), Return / refund rate (0.04), % new reach (0.03)
  - Fix via: email-sms.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); site CRO (low-ticket.md / high-ticket.md landing & PDP sections); post-purchase.md + email-sms.md
**Retargeting pool** — _Warm re-marketable audience size (KEYSTONE)._
  - Direct causes (strongest first): Reach (unique) (+0.6, ~1wk), Product page views (+0.4, ~1wk)
  - Levers to pull (root inputs): CPM (0.30), UGC / influencer reach (0.30), PDP view rate (0.20), Return / refund rate (0.10), % new reach (0.08), Time between orders (0.08)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); site CRO (low-ticket.md / high-ticket.md landing & PDP sections); post-purchase.md + email-sms.md
**Add-to-cart volume** — _Count of add-to-carts._
  - Direct causes (strongest first): Product page views (+0.6)
  - Levers to pull (root inputs): PDP view rate (0.30), % new reach (0.13), CPM (0.08), UGC / influencer reach (0.08), Return / refund rate (0.03), Time between orders (0.02)
  - Fix via: site CRO (low-ticket.md / high-ticket.md landing & PDP sections); tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
**List size** — _Total active subscribers._
  - Direct causes (strongest first): List growth rate (+0.7, ~1wk)
  - Levers to pull (root inputs): SMS opt-in rate (0.42), Quiz completion (0.24), Lead-magnet uptake (0.24), % new reach (0.19), CPM (0.12), UGC / influencer reach (0.12)
  - Fix via: list-building.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md)
**Email open rate** — _Opens / sends._
  - Direct causes (strongest first): Deliverability (+0.6)
  - Levers to pull (root inputs): Deliverability (0.60)
  - Fix via: email-sms.md
**Email click rate** — _Clicks / sends._
  - Direct causes (strongest first): Email open rate (+0.6)
  - Levers to pull (root inputs): Deliverability (0.36)
  - Fix via: email-sms.md
**Flow click rate** — _Automated-flow engagement._
  - Direct causes (strongest first): Email click rate (+0.5)
  - Levers to pull (root inputs): Deliverability (0.18)
  - Fix via: email-sms.md

### AOV
**AOV** — _Average order value._
  - Direct causes (strongest first): Units per order (+0.6), Upsell take rate (+0.55), Avg selling price (+0.5), Cross-sell attach rate (+0.5), Bundle adoption (+0.5), Free-ship threshold offer (+0.45), Subscription attach (+0.4), BNPL adoption (+0.4), Discount depth (+0.3), Gift-with-purchase (+0.3)
  - Levers to pull (root inputs): Upsell take rate (0.55), Avg selling price (0.50), Cross-sell attach rate (0.50), Bundle adoption (0.50), Free-ship threshold offer (0.45), Subscription attach (0.40)
  - Fix via: low-ticket.md (AOV) + high-ticket.md (BNPL) + post-purchase.md (upsell)
**Units per order** — _Items per transaction._
  - Direct causes (strongest first): Cross-sell attach rate (+0.5), Bundle adoption (+0.5), Upsell take rate (+0.4)
  - Levers to pull (root inputs): Cross-sell attach rate (0.50), Bundle adoption (0.50), Upsell take rate (0.40)
  - Fix via: low-ticket.md (AOV) + high-ticket.md (BNPL) + post-purchase.md (upsell)

### Retention
**Repeat purchase rate** — _% of customers ordering again._
  - Direct causes (strongest first): 30/60/90-day repeat (+0.6, ~4wk), Loyalty participation (+0.5, ~4wk), NPS / CSAT (+0.4, ~4wk)
  - Levers to pull (root inputs): 30/60/90-day repeat (0.60), Loyalty participation (0.50), NPS / CSAT (0.40)
  - Fix via: post-purchase.md + email-sms.md
**Customer LTV** — _Lifetime value per customer._
  - Direct causes (strongest first): Repeat purchase rate (+0.6), Purchase frequency (+0.6), Return / refund rate (−0.5)
  - Levers to pull (root inputs): Return / refund rate (0.50), Time between orders (0.36), 30/60/90-day repeat (0.36), Replenishment rate (0.30), Loyalty participation (0.30), NPS / CSAT (0.24)
  - Fix via: post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Return / refund rate
**Purchase frequency** — _Orders per customer per period._
  - Direct causes (strongest first): Time between orders (−0.6), Replenishment rate (+0.5, ~4wk)
  - Levers to pull (root inputs): Time between orders (0.60), Replenishment rate (0.50)
  - Fix via: post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Time between orders
**Active subscriptions** — _Live subscription count._
  - Direct causes (strongest first): Subscription churn (−0.6), Subscription attach (+0.5, ~2wk)
  - Levers to pull (root inputs): Subscription churn (0.60), Subscription attach (0.50)
  - Fix via: post-purchase.md + email-sms.md; low-ticket.md (AOV) + high-ticket.md (BNPL) + post-purchase.md (upsell)
  - ⚠ Culprit-when-high (negative drivers): Subscription churn
**Referral rate** — _Customers referring others._
  - Direct causes (strongest first): NPS / CSAT (+0.4, ~4wk), Loyalty participation (+0.3, ~4wk)
  - Levers to pull (root inputs): NPS / CSAT (0.40), Loyalty participation (0.30)
  - Fix via: post-purchase.md + email-sms.md
**Post-purchase flow revenue** — _Lifecycle email/SMS revenue._
  - Direct causes (strongest first): Flow click rate (+0.6, ~2wk)
  - Levers to pull (root inputs): Deliverability (0.11)
  - Fix via: email-sms.md

### TOF
**Branded search** — _Searches for the brand name (KEYSTONE)._
  - Direct causes (strongest first): Reach (unique) (+0.55, ~5wk), Share of voice (+0.5, ~5wk), Email click rate (+0.4, ~3wk), Watch time (+0.4, ~5wk), Follower growth (+0.4, ~8wk), UGC / influencer reach (+0.4, ~5wk)
  - Levers to pull (root inputs): Follower growth (0.40), UGC / influencer reach (0.40), CPM (0.28), Review submission rate (0.20), Deliverability (0.14), Return / refund rate (0.10)
  - Fix via: tof-strategy.md (branded search → measurement.md); tof-strategy.md / scaling-frequency.md; post-purchase.md + email-sms.md; email-sms.md
**Reach (unique)** — _Unique people reached._
  - Direct causes (strongest first): Prospecting spend (+0.7), Impressions (+0.6), CPM (−0.5), UGC / influencer reach (+0.5), Referral rate (+0.3, ~4wk)
  - Levers to pull (root inputs): CPM (0.50), UGC / influencer reach (0.50), Return / refund rate (0.17), Time between orders (0.13), 30/60/90-day repeat (0.13), NPS / CSAT (0.12)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): CPM
**New-visitor sessions** — _First-time visits._
  - Direct causes (strongest first): Ad CTR (+0.6), Reach (unique) (+0.6, ~2wk), % new reach (+0.5, ~1wk), CPC (−0.5)
  - Levers to pull (root inputs): % new reach (0.50), CPM (0.30), UGC / influencer reach (0.30), Return / refund rate (0.10), Time between orders (0.08), 30/60/90-day repeat (0.08)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): CPC
**Frequency** — _Avg impressions per person; too high = fatigue._
  - Direct causes (strongest first): Impressions (+0.5), Reach (unique) (−0.45)
  - Levers to pull (root inputs): CPM (0.23), UGC / influencer reach (0.23), Return / refund rate (0.10), Time between orders (0.07), 30/60/90-day repeat (0.07), Replenishment rate (0.06)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Reach (unique)
**Ad CTR** — _Click-through rate on ads._
  - Direct causes (strongest first): Hook rate (+0.6), Frequency (−0.4)
  - Levers to pull (root inputs): Creative volume (0.12), CPM (0.09), UGC / influencer reach (0.09), Return / refund rate (0.04), Time between orders (0.03), 30/60/90-day repeat (0.03)
  - Fix via: creative-testing.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Frequency
**Prospecting spend** — _Budget pushed to cold / new audiences._
  - Direct causes (strongest first): Customer LTV (+0.5, ~8wk)
  - Levers to pull (root inputs): Return / refund rate (0.25), Time between orders (0.18), 30/60/90-day repeat (0.18), Replenishment rate (0.15), Loyalty participation (0.15), NPS / CSAT (0.12)
  - Fix via: post-purchase.md + email-sms.md
**Impressions** — _Total ad views served._
  - Direct causes (strongest first): Prospecting spend (+0.8)
  - Levers to pull (root inputs): Return / refund rate (0.20), Time between orders (0.14), 30/60/90-day repeat (0.14), Replenishment rate (0.12), Loyalty participation (0.12), NPS / CSAT (0.10)
  - Fix via: post-purchase.md + email-sms.md
**Creative diversity** — _Spread of angles & formats in rotation._
  - Direct causes (strongest first): Creative volume (+0.5)
  - Levers to pull (root inputs): Creative volume (0.50)
  - Fix via: creative-testing.md
**Hook rate** — _3-second view %; opening strength._
  - Direct causes (strongest first): Creative diversity (+0.4)
  - Levers to pull (root inputs): Creative volume (0.20)
  - Fix via: creative-testing.md
**Hold rate** — _Thruplay / retention through the ad._
  - Direct causes (strongest first): Hook rate (+0.5)
  - Levers to pull (root inputs): Creative volume (0.10)
  - Fix via: creative-testing.md
**Watch time** — _Avg seconds viewed._
  - Direct causes (strongest first): Hold rate (+0.6)
  - Levers to pull (root inputs): Creative volume (0.06)
  - Fix via: creative-testing.md
**CPC** — _Cost per click._
  - Direct causes (strongest first): Ad CTR (−0.5)
  - Levers to pull (root inputs): Creative volume (0.06), CPM (0.05), UGC / influencer reach (0.05), Return / refund rate (0.02), Time between orders (0.01), 30/60/90-day repeat (0.01)
  - Fix via: creative-testing.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
  - ⚠ Culprit-when-high (negative drivers): Ad CTR
**Landing-page-view rate** — _Clicks that actually load the page._
  - Direct causes (strongest first): Ad CTR (+0.4)
  - Levers to pull (root inputs): Creative volume (0.05), CPM (0.04), UGC / influencer reach (0.04), Return / refund rate (0.02), Time between orders (0.01), 30/60/90-day repeat (0.01)
  - Fix via: creative-testing.md; tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
**Direct traffic** — _Type-in / bookmark visits (KEYSTONE)._
  - Direct causes (strongest first): Reach (unique) (+0.4, ~5wk)
  - Levers to pull (root inputs): CPM (0.20), UGC / influencer reach (0.20), Return / refund rate (0.07), Time between orders (0.05), 30/60/90-day repeat (0.05), NPS / CSAT (0.05)
  - Fix via: tof-strategy.md / scaling-frequency.md; tof-strategy.md (branded search → measurement.md); post-purchase.md + email-sms.md
**Referral traffic** — _Visits from other sites & links._
  - Direct causes (strongest first): Referral rate (+0.5, ~4wk)
  - Levers to pull (root inputs): NPS / CSAT (0.20), Loyalty participation (0.15)
  - Fix via: post-purchase.md + email-sms.md
**Share of voice** — _Brand mention share vs category._
  - Direct causes (strongest first): Review submission rate (+0.4, ~4wk)
  - Levers to pull (root inputs): Review submission rate (0.40)
  - Fix via: post-purchase.md + email-sms.md

## Worked example

**Revenue down 12%, sessions flat.** Step 2 (spine): sessions flat → the move is in **CVR**, not traffic. Step 3 (walk upstream from CVR): top causes are checkout completion (+0.8) and cart abandonment (−0.75, a negative driver) — check whether abandonment **spiked**. It did. Step 4 (reach lever): abandonment traces to checkout friction / site speed / trust. Step 5: confirm tracking is intact (measurement.md), then fix via CRO / low-ticket.md checkout section; watch checkout-completion rate recover before expecting revenue to follow.

## Sources

- funnel-decomposition.md — the revenue tree & identity-vs-signal epistemics (canonical)
- benchmarks.md — thresholds that define "off" (canonical)
- measurement.md — tracking validation, attribution, incrementality (canonical)
- Channel chunks — fix tactics: creative-testing.md, tof-strategy.md, list-building.md, email-sms.md, post-purchase.md, low-ticket.md, high-ticket.md, scaling-frequency.md
