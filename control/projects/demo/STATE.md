# State
## Phase
- Plan
## Objective
- Plan V2 (ambition): memory compaction + agent loop (AG/MCP) + packaging (optional)
## Now
- V1 local dev release shipped (stable)
- Start V2 planning (issues + acceptance criteria)
## Next
- Create V2 issues (0009/0010/0011)
- Decide V2 order of operations (reco: memory compaction -> agent loop -> packaging)
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
