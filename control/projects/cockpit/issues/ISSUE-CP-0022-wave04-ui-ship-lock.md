# ISSUE-CP-0022 - Wave04 UI ship lock

- Owner: leo
- Phase: Implement
- Status: Done

## Objective
- Lock UI render and CP-0015 evidence lane for ship readiness.

## Scope (In)
- app/ui/agents_grid.py
- app/ui/theme.qss
- docs/reports/CP01_UI_EVIDENCE_DELTA_P0.md
- docs/reports/CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md

## Scope (Out)
- backend MCP changes
- tournament files

## Done (Definition)
- QA matrix complete and coherent.
- Degraded-state capture mapped.
- No critical UI regression.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_status_model_v4.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_context_startup.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-LEO-WAVE04.md
