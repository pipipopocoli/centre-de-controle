# ISSUE-CP-0045 - Wave13 Vulgarisation Simple Clean

- Owner: nova
- Phase: Implement
- Status: Done

## Objective
Make Simple mode truly readable in <=60s while keeping Tech mode complete.

## Scope (In)
- `app/services/project_bible.py`
- `app/ui/project_bible.py`
- `app/ui/theme.qss`

## Done (Definition)
- [x] Simple mode uses strict blocks: On est ou / On va ou / Pourquoi / Comment.
- [x] What next list limited to max 5 actions.
- [x] Timeline limited to top 8 rows in Simple.
- [x] Tech mode still includes full evidence tables.

## Closeout
- Closed at: 2026-02-23T07:29Z
- Proof pack:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0044_CP0045_PROOF_2026-02-23T0729Z.md`
- Validation highlights:
  - strict brief block present (`On est ou / On va ou / Pourquoi / Comment`)
  - `what_next_rows=3` (<=5)
  - `timeline_rows_simple=7` (<=8)
  - tech sections present: `architecture-overview`, `progress-panel`, `cost-usage`, `skill-inventory`
- Tests green:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_accessibility.py`

## Now / Next / Blockers
- Now: CP-0044/CP-0045 closed with proof pack and green tests.
- Next: keep 2h cadence updates and watch freshness/pulse drift.
- Blockers: none.

## Notes
- No tournament changes.
