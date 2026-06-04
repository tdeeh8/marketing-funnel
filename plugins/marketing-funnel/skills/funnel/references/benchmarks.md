# Benchmark Ceilings (for Headroom)

The `benchmark` column in the values file = the **"strong" ceiling** the lever is measured against (headroom = distance to it). These are pragmatic 2025–2026 DTC ranges for the mappable rate levers. If you maintain your own vertical benchmark library, prefer those thresholds and the client's standing context; the table here is the standalone fallback so the skill works on its own.

Pick the column by AOV tier (from `clients/{Client}/CLAUDE.md`). Values are the "strong" target; volume levers (sessions, list size, reach) have no universal ceiling — use the account's own trailing best or a growth target instead of a fixed number.

| Lever | good dir | Low (<$100) | Mid ($100–200) | High ($200+) |
|---|---|---|---|---|
| Sitewide CVR (cvr/cvr_id) | higher | 3.5% | 2.5% | 1.5% |
| New-visitor CVR | higher | 2.5% | 1.8% | 1.0% |
| Returning-visitor CVR | higher | 7% | 6% | 4% |
| Mobile CVR | higher | 3.0% | 2.0% | 1.2% |
| Checkout completion | higher | 75% | 72% | 68% |
| Cart abandonment | lower | 65% | 68% | 70% |
| Checkout abandonment | lower | 25% | 28% | 32% |
| PDP view rate | higher | 55% | 50% | 45% |
| Add-to-cart rate | higher | 12% | 10% | 8% |
| Initiate-checkout rate | higher | 45% | 42% | 38% |
| Bounce rate | lower | 35% | 40% | 45% |
| Site speed (LCP, lower better) | lower | 2.5s | 2.5s | 2.5s |
| Email capture rate | higher | 4% | 4% | 5% |
| Email open rate | higher | 40% | 40% | 42% |
| Email click rate | higher | 2.0% | 2.0% | 2.5% |
| Hook rate (3s) | higher | 30% | 28% | 25% |
| Ad CTR | higher | 1.5% | 1.2% | 1.0% |
| Frequency | lower | 2.0 | 2.5 | 3.0 |
| Repeat purchase rate | higher | 30% | 27% | 22% |
| Return rate | lower | 8% | 10% | 12% |
| Subscription churn (monthly) | lower | 6% | 7% | 8% |
| AOV | higher | tier target | tier target | tier target |

Notes:
- Negative-driver rows (good dir = lower): the benchmark is the "acceptable floor" — headroom is how far CURRENT sits above it.
- Where a node isn't in this table, use the client's trailing 90-day best as the benchmark, or mark it unmeasured if no reference exists.
- These ceilings are intentionally conservative; calibrate to the client's vertical when you maintain your own benchmark library.
