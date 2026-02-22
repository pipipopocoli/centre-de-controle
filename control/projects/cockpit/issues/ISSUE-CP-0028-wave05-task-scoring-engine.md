# ISSUE-CP-0028 - Wave05 task scoring engine

- Owner: agent-3
- Phase: Implement
- Status: Done

## Objective
- Add deterministic task-to-agent ranking with weighted scoring.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py

## Scope (Out)
- Router execution logic
- Tournament files

## Done (Definition)
- `Score(A,T)=w1*SkillMatch+w2*Avail+w3*Cost+w4*History` implemented.
- Same input state returns same ranking order.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_runtime_conformance_l2.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-AGENT3-WAVE05.md
