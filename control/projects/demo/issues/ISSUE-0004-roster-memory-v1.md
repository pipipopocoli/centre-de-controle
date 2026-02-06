# ISSUE-0004 - roster + memory v1

- Owner: victor
- Phase: Implement
- Status: In progress

## Objective
- Ensure each project auto-creates a stable roster (clems/victor/leo) with canonical state.json and memory.md.

## Scope (In)
- Default roster creation (state.json + journal.ndjson + memory.md).
- Canonical state schema (engine/phase/percent/eta_minutes/heartbeat/status/blockers).
- Legacy read support (source/progress).
- Tests updated to verify roster and compatibility.

## Scope (Out)
- Codex App Server connector.
- UI redesign beyond roster display.

## Now
- Implement roster/backfill + memory template in store.
- Update model/UI/MCP server schema.

## Next
- Update tests + verify_mcp_basic.
- Run python tests/verify_mcp_basic.py.

## Blockers
- None.

## Done (Definition)
- Opening a project shows Clems + Victor + Leo without MCP updates.
- Each default agent has memory.md present.
- python tests/verify_mcp_basic.py passes.

## Links
- STATE.md:
- DECISIONS.md:
- PR:

## Risks
- Legacy state.json drift if not normalized everywhere.
