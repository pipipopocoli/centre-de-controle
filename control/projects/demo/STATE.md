# State
## Phase
- Implement
## Objective
- V2: packaging prototype (macOS .app) with local-first data path
## Now
- Packaging prototype docs + data path fallback shipped (ISSUE-0011)
## Next
- Run PyInstaller build + QA checklist (ISSUE-0011)
## In Progress
- ISSUE-0011 packaging research
## Blockers
- PyInstaller install failed (pip could not reach pypi)
## Risks
- Packaging drag (PySide6 bundling can be time-consuming)
- Memory contamination (cross-project) if retrieval is not scoped
- Runtime demo artifacts (tests modify state/chat) -> keep deterministic baseline
## Links
- ROADMAP.md
- DECISIONS.md
- Issues: control/projects/demo/issues/
