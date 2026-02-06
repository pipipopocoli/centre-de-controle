# State
## Phase
- Implement
## Objective
- V2: deliver memory compaction, then agent loop (AG/MCP)
## Now
- Memory compaction tool shipped (ISSUE-0009)
## Next
- Start ISSUE-0010 (agent loop e2e)
- Optional later: ISSUE-0011 packaging research
## In Progress
- None
## Blockers
- None declared
## Risks
- Packaging drag (PySide6 bundling can be time-consuming)
- Memory contamination (cross-project) if retrieval is not scoped
- Runtime demo artifacts (tests modify state/chat) -> keep deterministic baseline
## Links
- ROADMAP.md
- DECISIONS.md
- Issues: control/projects/demo/issues/
