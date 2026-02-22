# ISSUE-CP-0037 - Wave09 pilotage control badges

- Owner: leo
- Phase: Implement
- Status: Done

## Objective
- Surface dual-root control status clearly in Pilotage and timeline views.
- Ensure operator can instantly see repo/app health in Simple and Tech modes.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`

## Scope (Out)
- Backend cadence logic
- Tournament changes
- New network dependencies

## Done (Definition)
- [x] Repo/AppSupport control status badges are visible and unambiguous.
- [x] Simple and Tech modes both expose control state with expected detail depth.
- [x] Evidence pack maps screenshot captures to scenario IDs.
- [x] Degraded-state example is included and labeled.

## Test/QA
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/verify_ui_polish.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_hybrid_timeline.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_accessibility.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md`

## Decision note (2026-02-20)
- Leo latest status confirms lane independence and no blocker:
  - source message: `msg_20260220_163151_814984_leo_2980`
- Decision:
  - keep CP-0037 active and move to `In Progress`
  - require Wave09 closeout evidence mapping (repo/app badges, simple/tech, degraded case) before `Done`

## Resolution note (2026-02-21)
- UI Badges implemented in Pilotage (`project_pilotage.py`) and Styled (`theme.qss`). Evidence locked in `CP01_UI_WAVE07_EVIDENCE.md` and `CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md`. Status set to Done.
