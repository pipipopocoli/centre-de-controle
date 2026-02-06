# Roadmap

## Now
- V1 local dev release shipped (stable + fast iteration)
- V2 planning: pick 2 epics to start (memory + agent loop)

## Next
- ISSUE-0009: Memory compaction tool (V2)
- ISSUE-0010: Agent loop e2e (AG/MCP) so pings can lead to real replies
- ISSUE-0011: Packaging research (macOS .app) (V2, optional)

## Risks
- Scope creep (keep V2 as small, testable PRs)
- Packaging drag (PySide6 bundling can be time-consuming)
- Memory contamination (cross-project) if retrieval is not scoped
- Schema drift (state.json / phases) if not enforced by tests
