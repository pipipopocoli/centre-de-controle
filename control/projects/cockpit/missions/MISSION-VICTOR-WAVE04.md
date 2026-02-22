# Mission - Clems to Victor - Wave04 Backend Contract Lock

Objective
- Lock backend contract lane for Wave04 (MCP + memory determinism).

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_skills_tools.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_project_routing_strict.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_compaction.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0023-wave04-backend-contract-lock.md

Scope (Out)
- UI layout work
- tournament files

Files allowed
- /Users/oliviercloutier/Desktop/Cockpit/app/**
- /Users/oliviercloutier/Desktop/Cockpit/control/**
- /Users/oliviercloutier/Desktop/Cockpit/tests/**

Done
- MCP tools contract stable and verified.
- Deterministic memory proof complete (2 consecutive runs).
- Status posted every 2h in Now/Next/Blockers.

Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_skills_tools.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_project_routing_strict.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_index.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_compaction.py`

Risks
- Contract drift in MCP payload.
- Hidden non-deterministic ordering.

Delegation
- @agent-1 owns MCP contract checks.
- @agent-3 owns deterministic memory checks.
