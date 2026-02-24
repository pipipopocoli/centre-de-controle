# ISSUE-CP-0060 - Wave16 Nova Retention Operator Digest

- Owner: nova
- Phase: Ship
- Status: Done

## Objective
Publish a retention-first operator digest aligned to codex-only operations.

## Scope (In)
- `app/services/project_bible.py`
- `control/projects/cockpit/agents/nova/memory.md`
- `docs/reports/WAVE16_RETENTION_VISIBILITY_ADVISORY_2026-02-23.md`
- `control/projects/cockpit/runs/retention/retention_status.json`

## Done (Definition)
- [x] Brief <=60s contains owner, next action, evidence, decision tag.
- [x] Retention tier visibility is explicit (7d/30d/90d/permanent).
- [x] One deep RnD recommendation is included for current phase.

## Constraints
- no provider routing redesign
- keep strict project isolation

## Closeout
- Closed at: 2026-02-24T00:00:00Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE16_RETENTION_VISIBILITY_ADVISORY_2026-02-23.md`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`
