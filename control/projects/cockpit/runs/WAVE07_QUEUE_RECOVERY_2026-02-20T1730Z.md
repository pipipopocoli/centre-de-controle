# Wave07 Queue Recovery - Victor lane

## Objective
- Fix duplicate queue generation and restore clean dispatch signal.
- Lock runtime/log coherence with explicit recovery contract.

## Scope
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/requests.ndjson
- /Users/oliviercloutier/Desktop/Cockpit/tests/

## Contract Implemented
- `recover_queue_state(projects_root, project_id, persist=True, now=None)` added in auto-mode.
- Dedup policy in recovery:
  - keep latest queued request per `(source_message_id, agent_id)`
  - close older duplicates with `closed_reason=duplicate_recovery`
- Exact duplicate line policy:
  - keep latest row per `request_id` in `requests.ndjson`
- Runtime/log sync policy:
  - if runtime request is open but latest log row is `closed`, runtime row is auto-closed
  - close reason priority: log `closed_reason`, fallback `queue_hygiene_runtime_recovery`
- Recovery integrated at start of `dispatch_once(...)`.
- `compute_control_gate_snapshot(...)` now uses post-recovery runtime view (`persist=False`) and exposes recovery source stats.

## Before / After (cockpit one-shot)
- Before recovery:
  - `requests.ndjson`: total=48, queued=4, open_like=4, duplicate_request_id=0, duplicate_keys=0
  - `auto_mode_state.json`: open=19 (`queued=16`, `dispatched=3`)
- Recovery execution result:
  - `runtime_synced_closed=15`
  - `exact_dupes_removed=0`
  - `semantic_dupes_closed=0`
  - `duplicate_groups_closed=0`
  - blockers: none
- After recovery:
  - `requests.ndjson`: total=48, queued=4, open_like=4
  - `auto_mode_state.json`: open=4 (`queued=4`, `dispatched=0`)

## Gate Snapshot (post-fix)
- `queued_runtime_requests=4`
- `pending_stale_gt24h=0`
- `stale_heartbeats_gt1h=8`
- sources:
  - `runtime_sync_closed_count=0` (already synchronized before snapshot)
  - `duplicate_groups_closed_count=0`
  - `queue_recovery_blockers=[]`

## Test Evidence
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode.py`
  - `OK: auto-mode runner verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
  - `OK: wave07 control gate snapshot verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py`
  - `OK: wave07 queue recovery verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave05_dispatch.py`
  - `[PASS] deterministic tie-break agent_id/request_id`
  - `[PASS] queue_target cap enforced`
  - `[PASS] hard cap enforced`
  - `[PASS] strict overload cap enforced`
  - `OK: wave05 dispatch scoring/backpressure verified`
- safety:
  - `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_execution_router.py`
  - `OK: execution router verified`

## No Tournament Drift
- `git diff --name-only | rg 'tournament'` -> no match

## Now / Next / Blockers
- Now:
  - Queue recovery contract landed in backend.
  - Runtime stale open drift reduced from 19 -> 4 via log->runtime sync.
  - Recovery tests green (auto_mode/control_gates/wave07_queue_recovery/wave05_dispatch).
- Next:
  - Keep 2h cadence checks and monitor new queued inflow.
  - Triage remaining 4 queued live requests through normal dispatch/reply loop.
  - Re-run gate snapshot after next cycle.
- Blockers:
  - `queued_runtime_requests=4` (>3 target) from active live queue, not duplicates.
  - `stale_heartbeats_gt1h=8` (out-of-scope blocker still active).
