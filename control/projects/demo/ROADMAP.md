# Roadmap

## Now
- V1 local dev release shipped (stable + fast iteration)
- V2: memory compaction + agent loop e2e shipped
- V2: packaging prototype in progress (ISSUE-0011)
- V2.1: Clems auto-reply + steps clarity (ISSUE-0012)
- V2.2: roadmap clarity + UI QA (ISSUE-0013)

## Next
- ISSUE-0011: Packaging research (macOS .app) (V2, optional)
- ISSUE-0012: Clems auto-reply + personas split (V2.1)
- ISSUE-0013: Roadmap clarity + UI QA (V2.2)

## Risks
- Scope creep (keep V2 as small, testable PRs)
- Packaging drag (PySide6 bundling can be time-consuming)
- Memory contamination (cross-project) if retrieval is not scoped
- Schema drift (state.json / phases) if not enforced by tests
