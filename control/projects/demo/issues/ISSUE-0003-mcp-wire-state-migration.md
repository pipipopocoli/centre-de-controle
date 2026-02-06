# ISSUE-0003 - MCP Wire + state.json Migration (V1)

- Owner: victor (@victor)
- Phase: Ship
- Status: Done

## Objective
- Make MCP integration coherent end-to-end: chat messages visible in UI, and agent state uses a canonical schema.

## Scope (In)
- Canonical state.json schema for agent grid:
- engine (CDX/AG), phase, percent, eta_minutes, heartbeat, status, blockers.
- Backward compatibility: accept old fields (source/progress/current_phase) and write canonical schema.
- MCP chat wiring:
- cockpit.post_message writes to control/projects/<id>/chat/global.ndjson and thread files from tags.
- Normalize phase vocabulary to Plan/Implement/Test/Review/Ship everywhere (store, UI, server, tests).
- Update tests: tests/verify_mcp_basic.py and tests/test_mcp_server.py.

## Scope (Out)
- Full production quota tracking (get_quotas can stay mock for now).

## Now
- Merged to main (2026-02-06).

## Next
- None.

## Blockers
- None

## Done (Definition)
- After calling cockpit.update_agent_state, UI shows:
- engine, phase, percent, eta_minutes, heartbeat, status, blockers.
- After calling cockpit.post_message, message appears in UI global feed (and threads for tags).
- python3 tests/verify_mcp_basic.py passes.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR: Merged: codex/mcp-wire-state-migration -> main (2026-02-06)

## Risks
- Breaking client payloads (keep compat + tests).
