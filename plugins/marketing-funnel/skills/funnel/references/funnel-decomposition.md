# Full-Funnel Revenue Decomposition

Last updated: 2026-05-29. Sources: Common Thread Collective (revenue layers / ecommerce diagnostic), Measured & Sellforte (MMM marginal-ROI), Triple Whale (benchmarks), Northbeam (Clicks + Views), internal client-learnings system. Status: SPEC / backbone chunk — ties the channel chunks together; does not own platform thresholds (see benchmarks.md) or attribution (see measurement.md).

> **Why this chunk exists.** Most playbooks — and most of our own skills — are bottom-funnel heavy, because the bottom funnel is *measurable* (same-session, attributable). But bottom-funnel metrics don't *create* revenue; they *convert demand that already exists*. Durable revenue growth comes from growing the demand pool (TOF) and moving it down efficiently (MOF). This chunk is the map: every revenue metric, its parent, and the lag between the upstream cause and the downstream dollar. It is the spec we build cross-account analysis and TOF/MOF skills against.

---

## Core Methodology (Evergreen)

### The one idea: identity below, signal above

The funnel has **two different epistemic layers**, and the single biggest analytical mistake is treating them the same:

- **Bottom funnel is an *identity*.** Revenue, orders, AOV, CVR relate by definitional math. When one moves, the cause is deterministic and provable from a single account in a single period. Trust it immediately.
- **Top funnel is a *signal*.** Reach, creative engagement, branded search relate to revenue *statistically, with lag, and through noise*. A single account can't prove the link. It must be validated by replication across many accounts (and ideally incrementality). Never present a top-funnel correlation as causal from one account.

The middle funnel is the **bridge** — part identity (capture rates are math), part signal (the value of a captured asset shows up later).

### The three layers, defined by *what they do to demand*

Don't think "stages of a journey." Think **demand creation → demand capture → demand conversion**:

| Layer | Job | Epistemics | Typical lag to revenue |
|---|---|---|---|
| **TOF — Demand Creation** | Grow the *total pool* of people who want the product | Signal (statistical) | 3–8+ weeks (longer at high AOV) |
| **MOF — Demand Capture & Nurture** | Convert attention into a *re-marketable asset* (list, warm pool) and qualify intent | Bridge (part math, part signal) | days–weeks |
| **BOF — Demand Conversion** | Harvest *existing* intent into orders, efficiently | Identity (deterministic) | ~0 (same session–days) |

### The ceiling principle

BOF optimization has a hard ceiling: **the size of the current demand pool.** You can lift sitewide CVR from 2.1% → 2.6% and bank real money, but it's a one-time, capped gain — you're harvesting a fixed field better. To raise the ceiling you must feed the top. Corollary: *a brand that only optimizes BOF will plateau the moment its inherited demand is fully harvested.*

### New vs. returning is two different funnels

Split revenue at the top before decomposing:

```
Revenue = New-customer revenue + Returning-customer revenue
```

- **New-customer revenue** is driven by the acquisition funnel: TOF → MOF → BOF. This chunk owns it.
- **Returning-customer revenue** is driven by the *post-purchase / retention loop* (see post-purchase.md, email-sms.md), a separate engine. Conflating the two is why "blended CVR is up but we're not growing" goes undiagnosed.

---

## The Decomposition Tree

Read top-down (revenue → its parts). Each node lists its **parent**, the **layer** that moves it, and the **lag**.

### Level 0 — Output
```
Revenue  (Shopify = source of truth)
 ├── New-customer revenue        → acquisition funnel (this chunk)
 └── Returning-customer revenue  → retention loop (post-purchase.md)
```

### Level 1 — Proximate drivers (the two multiplicands)
```
New-customer revenue = New Orders × New AOV
```
- **Orders** — volume. Parent of everything in the acquisition funnel below.
- **AOV** — value per order. Mostly a BOF/offer lever; lag ≈ 0.

### Level 2 — Orders (the funnel spine)
```
Orders = Sessions × CVR
Sessions = Σ traffic by source (paid, organic, direct, email/SMS, referral, social)
CVR = f(traffic quality, site/PDP experience, offer, trust)
```
This is the identity hinge. **Sessions is fed by TOF+MOF; CVR is governed by MOF+BOF.** A revenue move is *always* localizable here first: was it Orders or AOV? If Orders — was it Sessions or CVR? If Sessions — which source? Do this deterministic localization *before* reaching for any upstream story.

### Level 2 — AOV (parallel branch)
```
AOV = Units per order × Avg selling price + attach revenue (upsell/cross-sell)
```
Levers (all BOF, lag ≈ 0): bundles, free-shipping thresholds, post-purchase upsells, subscription, BNPL. Owned operationally by low-ticket.md / high-ticket.md.

---

### Level 3 — BOF: Demand Conversion (identity, lag ≈ 0)

Converts existing demand. Multiplies Sessions into Orders.

| Metric | Parent | What moves it | Lag |
|---|---|---|---|
| Sitewide CVR | Orders | site speed, PDP, offer, trust | same session |
| PDP → Add-to-Cart rate | CVR | PDP quality, price clarity, social proof | same session |
| ATC → Initiate Checkout rate | CVR | cart UX, shipping surprise, urgency | same session |
| Initiate Checkout → Purchase (checkout completion) | CVR | checkout friction, payment options, trust badges | minutes–days |
| Cart/checkout abandonment (inverse of above) | CVR | same as above + abandonment flows | hours–days |
| Retargeting / branded-search CVR | CVR | warm-pool quality (built upstream) | same session |
| Attach / upsell take rate | AOV | offer construction | same session |

**Diagnostic role:** BOF is where you *confirm* a move is real (math closes) and where one-time efficiency lives. It is **not** where durable growth comes from.

### Level 3 — MOF: Demand Capture & Nurture (bridge, lag ≈ days–weeks)

Builds the re-marketable asset and qualifies intent. Feeds BOF a larger, warmer, higher-converting pool.

| Metric | Parent | What moves it | Lag |
|---|---|---|---|
| Add-to-Cart rate (first real intent) | CVR & warm pool | creative→offer match, PDP | same day |
| Email + SMS capture rate (% sessions → subscriber) | future email/SMS revenue | popups, quizzes, lead magnets | immediate capture, lagged payoff |
| **List / SMS net growth rate** (new subs/week) | future flow & campaign revenue | TOF volume × capture rate | 1–4 weeks to first flow revenue |
| Returning-visitor rate | CVR (returning visitors convert higher) | retargeting, email, brand pull | days–weeks |
| Retargeting pool size (warm audience) | BOF retargeting ROAS | TOF reach feeding the pool | days–weeks |
| Email/SMS engagement (open, click, flow CTR) | branded search & direct (warm intent) | content, segmentation, cadence | days |
| Engaged time / pages-per-session | CVR (consideration depth) | content, merchandising, page speed | same–next session |

**Why MOF is the most under-instrumented layer:** it's where the *asset* is built. A captured email or a warm retargeting cookie is revenue you haven't collected yet. Single-account evidence is usually enough to trust MOF moves (capture rate is math), but the *payoff* shows up downstream, so naive same-period analysis misses it.

### Level 3 — TOF: Demand Creation (signal, lag ≈ 3–8+ weeks)

Grows the total pool. Feeds MOF (new people to capture) and, later, BOF (new branded/direct intent).

| Metric | Parent | What moves it | Lag |
|---|---|---|---|
| New-audience reach / % new reach | future sessions & list growth | budget, targeting breadth, creative | weeks |
| Impressions & CPM (cost to create awareness) | reach | auction, creative, audience | immediate cost, lagged effect |
| Creative engagement: hook rate (3-sec %), hold/thumbstop, watch time | reach→site arrival | creative quality (see creative-testing.md) | days |
| New-visitor sessions | Sessions | reach × click quality | days–weeks |
| **Branded search volume** ⭐ | future high-intent BOF sessions | TOF working (demand created elsewhere returning as intent) | 3–8 weeks |
| **Direct traffic volume** ⭐ | future sessions | brand awareness, recall | 3–8 weeks |
| Organic/social follower & mention growth | reach & branded search | content, community, PR | weeks–months |

**Measurement reality:** most of TOF is *not* an identity. You cannot cleanly attribute a sale to an impression six weeks ago. So you lean on **keystone leading indicators** (below) that *are* measurable, and you validate the rest by replication + incrementality.

---

## Keystone Leading Indicators

These are the measurable proxies that bridge the unmeasurable. Track these and you can see the upper funnel working before revenue confirms it:

| Indicator | Answers | Leads revenue by |
|---|---|---|
| **Branded search volume** | "Is TOF *creating* demand?" | 3–8 weeks |
| **Direct traffic growth** | "Is brand recall building?" | 3–8 weeks |
| **List / SMS net growth rate** | "Is MOF *capturing* the demand?" | 1–4 weeks |
| **Retargeting pool size + returning-visitor rate** | "Is the warm pool growing?" | days–weeks |
| **New-vs-returning revenue split (trend)** | "Is the funnel feeding itself or just harvesting inherited demand?" | concurrent diagnostic |

> Rule of thumb: if you can only afford to instrument the top funnel with *five* metrics, use these five.

---

## The Lag Chain (how a TOF dollar becomes a BOF order)

```
Week 0    TOF spend → reach + creative engagement (hook rate, watch time)
Week 0–2  New sessions arrive → MOF captures them (ATC, email/SMS signup, retargeting cookie)
Week 1–4  List & warm pool grow → flow/retargeting revenue begins
Week 3–8  Branded search + direct traffic rise (demand created now returning as intent)
Week 3–12 High-intent BOF conversions land — and BOF metrics "take the credit"
```

The illusion this dispels: BOF looks like it's winning (high-CVR, low-CAC branded/retargeting conversions), but the *cause* was a TOF/MOF investment weeks earlier. This is why same-period attribution structurally under-credits the top and why **lag-aware, cross-account analysis is the only way to see it.**

High-AOV / high-consideration brands run on the long end of every lag window; impulse/low-AOV on the short end (see high-ticket.md / low-ticket.md).

---

## Diagnostic Signals (locate the constraint)

Use the identity spine first, then read the layer:

- **Revenue flat, CVR strong/improving, traffic falling** → **TOF problem.** You're harvesting a shrinking field. Feed the top.
- **Traffic growing, CVR falling, orders flat** → **MOF/BOF leak.** Either the new traffic is junk (TOF targeting/creative mismatch) or the site can't convert it. Check traffic quality + PDP/checkout.
- **New-customer revenue falling, returning steady** → **acquisition funnel broken** (TOF/MOF). Don't blame retention.
- **Returning revenue falling, new steady** → **retention loop problem**, not this funnel (→ post-purchase.md, email-sms.md).
- **CVR up but revenue flat for 6–8 weeks** → demand pool contracting; a BOF win is masking a TOF starvation. Check branded search trend.
- **Branded search + direct rising but orders flat** → demand is being created but **leaking in MOF/BOF**. Capture and conversion can't keep up with awareness.
- **List growth flat while reach grows** → MOF capture is the bottleneck (popup/lead-magnet/quiz). TOF is filling a leaky bucket.
- **Retargeting ROAS strong but declining over time** → warm pool shrinking because TOF reach is under-fed. Retargeting can't run on an empty top.

---

## Cross-Account Validation Methodology

How this spec becomes an evidence-backed playbook (ties to the client-learnings system):

1. **Build the identity spine per account/period** (deterministic). Revenue → Orders × AOV → Sessions × CVR → by source. This always closes; it's the skeleton.
2. **Detect material inflections** in revenue (already done by `client-learnings-data`).
3. **Localize deterministically first.** For each inflection, walk the identity tree: Orders or AOV? Sessions or CVR? Which source? This isolates *where* without any causal guessing.
4. **Test upstream signals at lag.** For the unexplained or upstream portion, cross-correlate TOF/MOF leading indicators against the revenue move at lags of 0–12 weeks. Record the best-fit lag and direction.
5. **Promote on replication, not on a single account.** A lever earns a place in the playbook only when the lagged relationship **repeats across N accounts** with consistent direction and a plausible magnitude — segmented by vertical / AOV tier (don't pool naively). Confirm causation with incrementality where stakes justify it (see measurement.md).
6. **Tag by epistemic class.** Identity moves = proven. MOF moves = trusted on single-account evidence. TOF moves = require cross-account replication + lag + (ideally) a geo-test.

This is the discipline that separates "we found a correlation on one client" from "this is a portfolio-validated growth lever."

---


## Sources

- Common Thread Collective — Ecommerce Analytics / Revenue Layers: https://commonthreadco.com/blogs/coachs-corner/ecommerce-analytics
- Measured — Real-Life MMM & Incrementality: https://www.measured.com/faq/real-life-media-mix-modeling-mmm-examples-true-incrementality/
- Sellforte — MMM for Ecommerce (marginal ROI): https://sellforte.com/marketing-mix-modeling-for-ecommerce
- Triple Whale — Ecommerce Benchmarks 2025: https://www.triplewhale.com/blog/ecommerce-benchmarks
- eMarketer — MMM tops the incrementality stack: https://www.emarketer.com/content/media-mix-modeling-tops-incrementality-measurement-stack-retail-brands
- Internal: measurement.md (attribution/incrementality, canonical), benchmarks.md (thresholds, canonical), client-learnings-data (inflection detection)
