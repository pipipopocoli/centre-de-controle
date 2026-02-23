# ISSUE-CP-0042 - Wave10 vulgarisation clean simple tech

- Owner: nova
- Phase: Implement
- Status: Done

## Objective
- Deliver a clean Simple view and complete Tech view for vulgarisation.
- Keep Brief 60s stable and action-first.
- Keep evidence links and offline rendering contract.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_bible.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`

## Scope (Out)
- Runtime router internals
- Tournament dispatch

## Done (Definition)
- [x] `Simple` view shows 4 primary cards max.
- [x] `Simple` includes explicit `What next` actions.
- [x] `Simple` timeline limited to top 8 rows.
- [x] `Tech` keeps full evidence tables and links.
- [x] Brief 60s keeps owner/action/evidence discipline.

## Verification
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
- `QT_QPA_PLATFORM=offscreen ./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_mode_split.py`

## Closeout
- Closed at: 2026-02-23T09:09Z
- Evidence packet:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0015_CP0042_CLOSEOUT_2026-02-23T0909Z.md`
- Validation highlights:
  - simple_primary_cards=0 (<=4)
  - simple_what_next_rows=3 (<=5)
  - simple_timeline_rows=7 (<=8)
  - tech sections present: `architecture-overview`, `progress-panel`, `cost-usage`, `skill-inventory`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_VULGARISATION_UPGRADE_WAVE07.md`
