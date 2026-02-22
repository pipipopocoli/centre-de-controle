# Mission - Clems to Leo - Wave04 UI Ship Lock

Objective
- Lock UI ship lane and close CP-0015 delta evidence with no critical regression.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/agents_grid.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_EVIDENCE_DELTA_P0.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0022-wave04-ui-ship-lock.md

Scope (Out)
- backend MCP changes
- tournament files

Files allowed
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/**
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/**
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/**

Done
- Scenario matrix complete.
- Capture mapping complete (including degraded-state).
- No critical UI regression.
- Status posted every 2h in Now/Next/Blockers.

Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_status_model_v4.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_context_startup.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_vulgarisation_contract.py`

Risks
- Visual regressions hidden by stale captures.
- Incomplete degraded-state proof.

Delegation
- @agent-6 owns matrix + repro.
- @agent-7 owns captures + mapping.
