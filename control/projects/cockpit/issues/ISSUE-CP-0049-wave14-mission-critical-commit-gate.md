# ISSUE-CP-0049 - Wave14 Mission Critical Commit Gate

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
Enforce mission-critical gate so no commit lands without required evidence and approval.

## Scope (In)
- `app/services/auto_mode.py`
- `scripts/auto_mode.py`
- `app/services/gatekeeper.py`
- `control/projects/cockpit/settings.json`

## Done (Definition)
- [x] Commit gate requires explicit approval marker for critical lane.
- [x] Required evidence checklist enforced: tests + screenshots + logs + docs update.
- [x] Blocker state prevents progression when critical gate is red.
- [x] Structured error/report when gate fails.

## Constraints
- no hidden bypass
- keep backward compatibility for non-critical lane

## Closeout
- Closed at: 2026-02-23T10:26Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE14_VICTOR_LANE_LOCK_2026-02-23T1026Z.md`
- Runtime evidence:
  - `runs/mission_critical_gate.ndjson` ledger enabled
