# ISSUE-0004 - Default roster + per-agent memory (V1)

- Owner: victor (@victor)
- Phase: Ship
- Status: Done

## Objective
- Every project auto-creates a stable default roster (clems/victor/leo) and per-agent memory files, isolated per project.

## Scope (In)
- On project creation, ensure default agent folders exist:
  - `control/projects/<id>/agents/clems/`
  - `control/projects/<id>/agents/victor/`
  - `control/projects/<id>/agents/leo/`
- For each agent, create if missing (do not overwrite):
  - `state.json` (canonical schema)
  - `memory.md` (template)
  - `journal.ndjson` (empty)
- Ensure legacy states still load (source/progress -> engine/percent).
- Update `tests/verify_mcp_basic.py` to assert default roster exists.

## Scope (Out)
- RAG / embeddings / vector DB.
- Cross-project retrieval.
- UI redesign (separate issue).

## Now
- Merged to main (2026-02-06).

## Next
- None.

## Blockers
- None.

## Done (Definition)
- New project shows clems/victor/leo immediately.
- `memory.md` exists for each agent.
- `journal.ndjson` exists for each agent.
- `./.venv/bin/python tests/verify_mcp_basic.py` passes.
- No regression in MCP chat persistence (NDJSON).

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR: Merged: codex/roster-memory-v1 -> main (2026-02-06)

## Risks
- Tests may generate local demo artifacts (keep demo scaffold deterministic).
