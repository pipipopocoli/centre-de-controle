# ISSUE-CP-0036 - Wave09 healthcheck contract hardening

- Owner: agent-3
- Phase: Implement
- Status: Done

## Objective
- Harden healthcheck behavior for elapsed-time and snapshot recency semantics.
- Ensure repeated runs with unchanged inputs produce deterministic verdicts.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode.py`

## Scope (Out)
- UI rendering changes
- Tournament artifacts
- New external APIs

## Done (Definition)
- [x] Deterministic verdict behavior verified over repeated runs.
- [x] `stale_tick` and `stale_kpi_snapshot` semantics are explicit and covered by tests.
- [x] No regression on queue-recovery/control-gates verification suites.
- [x] Proof report produced with command summaries.

## Closeout
- Closed at: 2026-02-20T22:21Z
- Evidence packets:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_RUNTIME_FINAL_LOCK_2026-02-20T2221Z.md`
- Tests executed (green):
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave09_dual_root_cadence.py`
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py`

## Test/QA
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_RUNTIME_FINAL_LOCK_2026-02-20T2221Z.md`

## Now / Next / Blockers
- Now: CP-0035/CP-0036 closed; repo+app healthy across two checkpoints; tests green.
- Next: keep 25-30m cadence; advance CP-0037 (Pilotage badges) and CP-0038 (advisory ledger).
- Blockers: none.
