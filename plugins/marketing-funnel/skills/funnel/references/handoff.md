# Handoff — lever → execution arm

Once the top lever(s) are identified, the prioritizer's job is to point the right tool at them. It does NOT execute the fix itself. Route by the lever's layer/domain:

| Top lever domain | Example levers | Execution arm | How to invoke |
|---|---|---|---|
| **Paid media** | prospecting spend, reach, frequency, CPM, CPC, hook/hold/watch, creative volume/diversity | **`/ads`** | `/ads audit {client}` (diagnose paid), `/ads plan` (reallocate), `/ads brief` (new creative for a hook/creative lever) |
| **List capture** | email/SMS capture rate, list growth, quiz, lead magnet, pop-ups | **`list-building.md`** (or `klaviyo-analyst`) | Load chunk; apply capture tactics |
| **Email/SMS nurture** | deliverability, open/click, flow CTR, post-purchase flow revenue | **`email-sms.md`** / `klaviyo-analyst` | Load chunk; flow + cadence fixes |
| **Site / CRO** | bounce, engaged time, PDP rate, add-to-cart rate, site speed, trust | **CRO sections of `low-ticket.md` / `high-ticket.md`** + `measurement.md` (verify tracking first) | Load chunk; PDP/landing/checkout fixes |
| **Checkout** | initiate-checkout rate, checkout completion, cart/checkout abandonment, payment success, express checkout | **`low-ticket.md` (checkout friction)** + `measurement.md` | Tracking gate, then friction fixes |
| **AOV / offer** | units per order, attach, upsell, bundle, subscription attach, free-ship threshold, BNPL | **`low-ticket.md` (AOV)** + **`post-purchase.md` (upsell)** | Offer construction |
| **Retention / LTV** | repeat rate, frequency, LTV, subscriptions, churn, loyalty, referral, reviews, returns | **`post-purchase.md` + `email-sms.md`** | Lifecycle + retention program |
| **Brand / organic demand** | branded search, direct, organic, share of voice, follower/UGC reach | **`tof-strategy.md`** (brand-building) + `measurement.md` (branded-search tracking) | Note: weakest-owned area; flag if it's the top lever |

Rules:
- If the top lever is **paid**, always hand to `/ads` — it has the per-platform depth this skill deliberately doesn't duplicate.
- If the top lever is a **tracking-dependent** rate (any CVR/checkout/abandonment metric), run the `measurement.md` tracking gate FIRST — a tracking break mimics a real drop and would send the fix in the wrong direction.
- End the run with ONE concrete next action ("Run `/ads plan {client}` to reallocate toward the prospecting-reach gap"), not a list of options.
