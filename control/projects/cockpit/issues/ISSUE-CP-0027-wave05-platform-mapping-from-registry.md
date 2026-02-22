# ISSUE-CP-0027 - Wave05 platform mapping from registry

- Owner: agent-1
- Phase: Implement
- Status: Done

## Objective
- Remove odd/even runtime mapping whenever registry exists.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/agent_registry.py

## Scope (Out)
- UI components
- Tournament files

## Done (Definition)
- Platform selection comes from registry for registered agents.
- Legacy odd/even mapping remains fallback-only.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_runtime_conformance_l2.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-AGENT1-WAVE05.md
