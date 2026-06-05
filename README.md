# Marketing Funnel — Biggest-Lever Prioritizer

A Claude plugin that answers one question with receipts: **given where this account actually is, what is the single biggest lever to grow revenue (and profit) — what do I change, what will it move, and why?**

It scores every lever across the entire funnel (TOF → MOF → BOF → AOV → Retention) using **Impact = Headroom × Sensitivity**, pulls live data so nothing is guessed, and runs a verification gate that blocks any ungrounded number, dollar figure, causal claim, or invented campaign name before a report can be built.

## Install

```
/plugin marketplace add marketing-funnel
/plugin install marketing-funnel@marketing-funnel
```

## Usage

| Command | What it does |
|---|---|
| `/funnel [client]` | Full run → ranked levers for revenue + profit, grounded plays, HTML gap brief + embedded live graph |
| `/funnel revenue [client]` or `/funnel profit [client]` | Same, single ranking |
| `/funnel backfill [client] [N weeks]` | Seed 12 weeks of history to unlock noise floors and trend tracking on day one |
| `/funnel diagnose <metric> [client]` | One metric is off → upstream walk to the root levers |
| `/funnel explain` | Explains the model and structural sensitivity ranking, no data pull |

Natural-language triggers also work: "what's my biggest lever", "where should I focus to grow profit", "what should I fix first".

## What it needs

- **Databox MCP** connected (Shopify/BigCommerce, GA4, Google Ads, Meta Ads data sources) — financial truth comes from Shopify, not paid attribution
- **Meta Ads MCP** (optional but recommended) — unlocks hook/hold/watch-time creative levers
- Klaviyo MCP via Databox connector (optional) — email/SMS levers
- Python 3 for the scoring, verification, report, and graph scripts

No ecommerce platform connected at all? The skill says so and labels everything directional rather than inventing numbers.

## How it stays honest

- Every number carries a `source` + `window`; missing data is written as `DATA_NOT_AVAILABLE`, never estimated
- Every dollar figure recomputes from a stated formula (exact identity math where possible, labelled priors otherwise)
- Every "why" is a real edge in a verified 88-node funnel graph
- Every recommended play names only campaigns/flows/offers that exist in the account's pulled inventory
- `scripts/verify.py` enforces all of the above and must exit 0 before any report is built
- An outcomes log self-calibrates predictions per account over time
- An embedded live funnel graph tracks every node period-over-period, applies per-node noise floors (learned from weekly history), and highlights real moves vs variance — built by `scripts/build_graph.py` and injected into every report

## Structure

```
plugins/marketing-funnel/
├── .claude-plugin/plugin.json
├── commands/funnel.md          ← /funnel command
└── skills/funnel/
    ├── SKILL.md                ← the orchestrator
    ├── references/             ← methodology, benchmarks, funnel graph (88 nodes), data-layer notes, graph template + layout
    ├── scripts/                ← score.py, verify.py, build_report.py, calibrate.py, build_graph.py
    └── tests/                  ← test_build_graph.py
```

## License

MIT
