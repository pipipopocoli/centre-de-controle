# ISSUE-CP-0042 - Wave10 vulgarisation clean simple tech

- Owner: nova
- Phase: Implement
- Status: In Progress

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
- [ ] `Simple` view shows 4 primary cards max.
- [ ] `Simple` includes explicit `What next` actions.
- [ ] `Simple` timeline limited to top 8 rows.
- [ ] `Tech` keeps full evidence tables and links.
- [ ] Brief 60s keeps owner/action/evidence discipline.

## Verification
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_VULGARISATION_UPGRADE_WAVE07.md`
