# State
## Phase
- Review
## Objective
- V2.1: Clems auto-reply + steps clarity + personas split
## Now
- QA Clems auto-reply + steps clarity (ISSUE-0012)
## Next
- Close ISSUE-0012 after QA
## In Progress
- ISSUE-0012 clems auto-reply
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
