# ISSUE-CP-0031 - Wave05 cost telemetry CAD

- Owner: agent-11
- Phase: Implement
- Status: Done

## Objective
- Emit CAD cost events per execution and expose monthly estimate.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/cost_events.ndjson

## Scope (Out)
- External billing integration
- Tournament files

## Done (Definition)
- `runs/cost_events.ndjson` populated with required fields.
- Monthly CAD estimate appears in vulgarisation output.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_bible.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_cost_telemetry.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-AGENT11-WAVE05.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP0031_COST_TELEMETRY_NOTE_2026-02-19.md
