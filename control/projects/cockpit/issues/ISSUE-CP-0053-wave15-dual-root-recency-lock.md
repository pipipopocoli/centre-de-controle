# ISSUE-CP-0053 - Wave15 Dual-Root Recency Lock

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
Harden runtime recency semantics for repo and AppSupport roots so stale-only false degraded states are removed after a fresh pulse.

## Scope (In)
- `scripts/auto_mode_healthcheck.py`
- `scripts/auto_mode.py`
- `scripts/auto_mode_core.py`
- `app/services/auto_mode.py`
- `tests/verify_auto_mode_healthcheck.py`

## Done (Definition)
- [x] Fresh pulse suppresses stale snapshot as blocking error (soft warning only).
- [x] `stale_tick` and `pulse_stale` still trigger degraded correctly.
- [x] Deterministic healthcheck tests pass.
- [x] Dual-root pulse/check commands documented with expected transitions.

## Constraints
- no tournament side effects
- no silent masking of real runtime failures

## Closeout
- Closed at: 2026-02-23T11:08Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_OPERATOR_RECENCE_RUNBOOK_2026-02-23.md`
