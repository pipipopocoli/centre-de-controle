# ACTIVE_L4 Workspace

Purpose
- Active execution lane for L4 Gauntlet (winners-only).
- L4 is a deep, multi-step round with 3 mandatory outputs per agent.

Dispatch gate
- Do not dispatch L4 until L3 winners are locked for:
  - F13
  - F14
  - F15

Roster rule
1. Entrants = winners of F13/F14/F15.
2. If odd, inject wildcard next free id (default `agent-18`).
3. Pair sequentially into F17/F18.

Mandatory outputs per entrant
1. `<agent_id>_SUBMISSION_V4_FINAL.md`
2. `<agent_id>_FINAL_HTML/index.html`
3. `<agent_id>_EVIDENCE_V4.json`

Workspace map
- AGENT_READMES/: per-entrant entrypoint docs
- FIGHT-17/PROMPTS and SUBMISSIONS
- FIGHT-18/PROMPTS and SUBMISSIONS
- HTML_REVIEW_PACK/: aggregation target for operator review

Rules lock
- Currency: CAD
- OpenClaw benchmark: mandatory online site + code/repo compare
- Secret scoring: numeric details hidden from agents
- Missing one mandatory output triggers veto risk
