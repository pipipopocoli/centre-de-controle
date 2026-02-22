# ISSUE-CP-0026 - Wave05 agent registry runtime

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Use `/agents/registry.json` as runtime source of truth for roster metadata and provider mapping.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/agent_registry.py
- /Users/oliviercloutier/Desktop/Cockpit/app/data/store.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_agent_registry.py

## Scope (Out)
- Tournament files
- UI redesign

## Done (Definition)
- `load_project()` merges state with registry metadata.
- Registry missing -> fallback roster still works.
- Registry roundtrip persisted via `save_project()`.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_registry.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE05.md
