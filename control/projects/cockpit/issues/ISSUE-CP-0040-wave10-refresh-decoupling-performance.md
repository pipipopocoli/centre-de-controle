# ISSUE-CP-0040 - Wave10 refresh decoupling performance

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Decouple refresh loops to improve UI fluidity and reduce heavy rebuilds.
- Keep chat fast without forcing full project reload every 5s.
- Throttle vulgarisation refresh to avoid expensive regeneration on each tick.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_bible.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`

## Scope (Out)
- Tournament activation
- Full architecture rewrite

## Done (Definition)
- [x] Separate timer cadence for chat/project/bible.
- [x] Bible refresh is throttled and on-demand aware.
- [x] Project refresh no longer forces chat rebuild.
- [x] No blocking regression on tabs switch.

## Verification
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`

## Closeout
- Closed at (UTC): `2026-02-22T18:13:56Z`

## Evidence
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave10_runtime_lane.py` -> `OK: wave10 runtime/backend lane verified` (includes `cp-0040` pass)
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py` -> `OK: vulgarisation verified`
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py` -> `OK: vulgarisation contract verified`
