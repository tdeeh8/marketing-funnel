---
description: Find the biggest revenue/profit lever across the entire funnel for a client, with grounded causal chains and plays
argument-hint: "[client] | revenue | profit | explain | diagnose <metric> | backfill [N weeks]"
---

Run the funnel-prioritizer skill at ${CLAUDE_PLUGIN_ROOT}/skills/funnel/SKILL.md with these arguments: $ARGUMENTS

Follow the SKILL.md exactly: resolve the client, pull live values with provenance, pull inventory, score with scripts/score.py, generate plays, run scripts/verify.py (must exit 0 before building any report), build the HTML gap brief and embedded live graph, then present the result with the causal chain explained in plain words and ONE concrete next action.

Modes: default = prioritize (full run); `backfill [N weeks]` = seed history.csv with last N complete weeks to unlock noise floors and trend tracking on day one.
