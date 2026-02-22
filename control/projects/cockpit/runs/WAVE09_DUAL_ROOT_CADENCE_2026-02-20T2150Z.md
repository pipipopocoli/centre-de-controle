# Wave09 Dual-Root Control Cadence - 2026-02-20T2150Z

## Objective
- Lock dual-root cadence so repo + AppSupport healthchecks stay green over repeated checkpoints.
- Finalize one canonical cadence command set.

## Scope
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/
- /Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/

## Contract lock implemented
- New cadence constants exported in auto_mode service:
  - CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES = 25
  - HEALTHCHECK_KPI_SNAPSHOT_MAX_AGE_SECONDS = 2100
- New helper exported:
  - emit_control_cadence_kpi_snapshot(...)
  - wraps emit_kpi_snapshot with post_chat=False and min-interval guard
- scripts/auto_mode.py:
  - new flags: --no-kpi-snapshot, --kpi-min-interval-minutes
  - auto snapshot emission enabled by default after each dispatch cycle
  - stable ops line emitted: KPI snapshot emitted=... reason=... snapshot_path=...
- scripts/auto_mode_healthcheck.py:
  - new flag: --max-snapshot-age-seconds (default 2100)
  - stale_kpi_snapshot gate now parameterized
  - payload now includes max_snapshot_age_seconds

## Baseline capture (this run)
- Repo healthcheck (strict gate): healthy
- AppSupport healthcheck (strict gate): healthy
- Historical Wave09 precheck blocker (`stale_kpi_snapshot`) remains tracked as prior risk and is now prevented by default snapshot cadence emission in pulse script.

## Test evidence
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py
  - OK: auto_mode healthcheck parity verified
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave09_dual_root_cadence.py
  - OK: wave09 dual-root cadence verified
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py
  - OK: wave07 control gate snapshot verified
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py
  - OK: wave07 queue recovery verified

## Checkpoint 1 (ops)
1. Repo pulse
- emitted=true, reason=emitted
2. App pulse
- emitted=false, reason=min_interval
3. Repo health
- status=healthy, open_requests_external=3, snapshot_age_seconds=12, issues=[]
4. App health
- status=healthy, open_requests_external=0, snapshot_age_seconds=196, issues=[]

## Checkpoint 2 (ops)
1. Repo pulse
- emitted=false, reason=min_interval
2. App pulse
- emitted=false, reason=min_interval
3. Repo health
- status=healthy, open_requests_external=3, snapshot_age_seconds=30, issues=[]
4. App health
- status=healthy, open_requests_external=0, snapshot_age_seconds=209, issues=[]

## Canonical cadence runbook (every 25-30 min)
1. Repo pulse
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify --kpi-min-interval-minutes 25
2. App pulse
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir app --once --max-actions 0 --no-open --no-clipboard --no-notify --kpi-min-interval-minutes 25
3. Repo healthcheck
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir repo --stale-seconds 3600 --max-open 3 --max-snapshot-age-seconds 2100
4. App healthcheck
- /Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir app --stale-seconds 3600 --max-open 3 --max-snapshot-age-seconds 2100

## Before/After stale reconcile proof (explicit)
### Lane A - dual-root stale snapshot drift
- Before (`WAVE09_PRECHECK_2026-02-20.md`):
  - AppSupport status: `degraded`
  - AppSupport issues: `["stale_kpi_snapshot"]`
  - AppSupport snapshot_age_seconds: `6562`
- After (latest strict healthchecks, 2026-02-20T22:21:03+00:00):
  - Repo status: `healthy`, issues: `[]`, snapshot_age_seconds: `7`, open_requests_external: `3`
  - AppSupport status: `healthy`, issues: `[]`, snapshot_age_seconds: `7`, open_requests_external: `1`

### Lane B - runtime<->ledger reconcile behavior
- Before fixture (`tests/verify_wave07_queue_recovery.py`):
  - runtime request `req_sync` is open (`status=queued`) while latest ledger row for `req_sync` is already `status=closed`.
- After assertions (test PASS):
  - `runtime_synced_closed == 1`
  - duplicate cleanup counters incremented (`queue_exact_dupe_removed_total`, `queue_semantic_dupe_closed_total`, `runtime_log_sync_closed_total`)
  - runtime request `req_sync` transitions to `status=closed` with preserved `closed_reason=runner_completed`

## Reconcile contract anchor (no behavior change)
- Canonical reconcile contract is `recover_queue_state` in `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`.
- Contract guarantees:
  - runtime open requests are synced to `closed` when latest ledger row is closed
  - runtime ghost opens missing from ledger are closed with `queue_hygiene_runtime_missing_log_recovery`
- This runbook update is documentation + verification only. No reconcile behavior changes are introduced here.

## No tournament impact
- Scope lock for this execution:
  - no file edits under `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
  - no file edits under `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`

## Now / Next / Blockers
- Now:
  - Wave09 cadence contracts are locked in code (snapshot auto emit + configurable snapshot age gate).
  - Dual-root checkpoints are healthy on two consecutive runs.
- Next:
  - Continue 25-30 min cadence in ops window.
  - Keep 2h status updates in STATE.md.
  - Move CP-0036/CP-0037 lanes with this runbook as fixed dependency.
- Blockers:
  - none in backend cadence lane.
