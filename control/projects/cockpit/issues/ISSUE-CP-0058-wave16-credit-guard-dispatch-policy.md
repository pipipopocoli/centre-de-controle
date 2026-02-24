# ISSUE-CP-0058 - Wave16 Credit Guard Dispatch Policy

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
Apply a temporary dispatch budget guard to preserve credits until Feb 26.

## Scope (In)
- `control/projects/cockpit/settings.json`
- `app/services/auto_mode.py`
- `scripts/auto_mode.py`

## Done (Definition)
- [x] Credit guard enabled with wave cap and reserve floor.
- [x] Effective action cap set to 1 for this wave.
- [x] Lead-first/no-fanout policy encoded in wave docs.

## Constraints
- no external billing API dependency
- no AG specialist fanout

## Closeout
- Closed at: 2026-02-24T00:00:00Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json`
  - `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`
