# State
## Phase
- Review
## Objective
- V2.2: packaging prototype + QA + roadmap clarity
## Now
- QA Clems auto-reply + steps clarity (ISSUE-0012)
- Packaging prototype build + QA (ISSUE-0011)
- Roadmap clarity review (ISSUE-0013)
## Next
- Close ISSUE-0012 after QA
- Close ISSUE-0011 after .app QA
## In Progress
- ISSUE-0012 clems auto-reply
- ISSUE-0011 packaging research
- ISSUE-0013 roadmap clarity
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
