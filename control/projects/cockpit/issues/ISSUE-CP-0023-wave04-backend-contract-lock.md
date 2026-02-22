# ISSUE-CP-0023 - Wave04 backend contract lock

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Lock backend MCP and memory contracts with deterministic proof.

## Scope (In)
- control/mcp_server.py
- app/services/memory_index.py
- tests/verify_mcp_skills_tools.py
- tests/verify_mcp_project_routing_strict.py
- tests/verify_memory_index.py
- tests/verify_memory_compaction.py

## Scope (Out)
- UI files
- tournament files

## Done (Definition)
- MCP tools callable with structured payload.
- Routing strict checks pass.
- Memory deterministic output verified by 2-run proof.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_skills_tools.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_project_routing_strict.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_index.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE04.md
