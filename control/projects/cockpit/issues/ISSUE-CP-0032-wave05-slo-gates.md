# ISSUE-CP-0032 - Wave05 SLO gates

- Owner: leo
- Phase: Implement
- Status: Done

## Objective
- Compute and display SLO gate verdict GO/HOLD from p95/p99/success metrics.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/slo_verdict_latest.json

## Scope (Out)
- Tournament files
- New backend APIs

## Done (Definition)
- SLO verdict artifact generated on runtime updates.
- SLO and cost signals visible in UI/vulgarisation outputs.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_bible.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-LEO-WAVE05.md
