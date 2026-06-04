# Play Generation — grounded strategy, not generic advice

A "play" is a specific move tied to the account's live setup. The difference between this skill and a generic audit is that plays name real campaigns, flows, and offers — and every play carries its causal chain. Plays are written to `plays.json` and then checked by `verify.py` before they can appear.

## Inputs you must pull first

For each top lever, pull the relevant inventory (not just the headline metric):
- **Paid levers** → Meta/Google campaign structure: campaign names, active creative count, frequency, audience type, status. (Meta MCP / Databox; reuse `/ads` data layer.)
- **List/email/retention levers** → Klaviyo flow inventory: which flows exist and their on/off status (Welcome, Abandoned Checkout, Win-back, Replenishment, etc.).
- **AOV levers** → Shopify offer setup: bundles live, upsell app present, subscription offered, free-ship threshold.

Write these to `clients/{Client}/funnel/{date}/inventory.csv` (`entity_id,type,name,attrs`). This file is the grounding set.

## How to write a play

Each play is an object:

```json
{
  "lever": "repeat",
  "primary": true,
  "text": "The Win-back flow is off; turn on a 45-day lapsed flow with a refill incentive.",
  "owner": "email-sms.md",
  "referenced_entities": ["Win-back"],
  "grounded": true,
  "target_metric": "repeat_rate",
  "intermediate_metric": "ret_rev",
  "outcome_metric": "revenue",
  "why": "Reactivating lapsed buyers lifts repeat rate, which feeds returning revenue and thus total revenue."
}
```

Rules (all enforced by `verify.py`):
- `referenced_entities` must be names that appear in `inventory.csv`. Never name a campaign/flow/offer you didn't read.
- `target_metric → intermediate_metric` must be a real graph edge; `intermediate_metric` must reach `outcome_metric`. Pull these from the lever's own chain in `levers.json` — don't invent a path.
- If you have no inventory for a lever, write at most one generic play with `grounded:false` and `referenced_entities:[]`, phrased as "connect [system] for a specific play." Do not fabricate specifics to look helpful.
- `owner` routes execution: paid → `/ads (brief|plan)`; list/email → `email-sms.md` / `list-building.md`; site/checkout → CRO sections of `low-ticket.md` / `high-ticket.md` + `measurement.md`; AOV → `low-ticket.md` / `post-purchase.md`; retention → `post-purchase.md` / `email-sms.md`.
- Prefer 1 `primary` play (the single best move) + at most 1–2 secondary. More than that is noise.

## Tactics come from the chunks

The *content* of a good play (what specifically to change) comes from the owning playbook chunk, not from this skill. Read the chunk for the lever's domain, combine it with the inventory gap, and write the play. The skill decides the lever; the chunk supplies the craft.
