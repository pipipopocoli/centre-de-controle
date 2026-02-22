# Wave07 Backend Hardening - 2026-02-19T1803Z

## Objective
- Lock backend hardening lane for Wave07 on router/dispatch/cost telemetry contracts and control gate snapshoting.

## Scope
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/cost_telemetry.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/

## Contract Table
- Cost schema version: `wave05_cost_event_v2`
- Cost validation error contract (`COST_EVENT_ERROR_CODES`):
- `cached_token_mismatch`
- `currency_not_cad`
- `event_not_object`
- `invalid_cached_input_tokens_negative`
- `invalid_cached_input_tokens_type`
- `invalid_cached_tokens_negative`
- `invalid_cached_tokens_type`
- `invalid_cost_cad_estimate_negative`
- `invalid_cost_cad_estimate_type`
- `invalid_elapsed_ms_negative`
- `invalid_elapsed_ms_type`
- `invalid_input_tokens_negative`
- `invalid_input_tokens_type`
- `invalid_output_tokens_negative`
- `invalid_output_tokens_type`
- `invalid_timestamp`
- `invalid_ts_type`
- `missing_agent_id`
- `missing_project_id`
- `missing_provider`
- `missing_run_id`
- `project_id_mismatch`
- `schema_version_mismatch`
- Router status contract (`ROUTER_RESULT_STATUS_CONTRACT`):
- `completed`
- `disabled`
- `dry_run`
- `failed`
- `launched`
- `policy_denied`
- `project_lock_rejected`
- `skipped_wrong_project`
- `timeout`
- Router completion source contract (`ROUTER_COMPLETION_SOURCE_CONTRACT`):
- `ag_launch_failed`
- `codex_exec`
- `codex_exec_failed`
- `launched_supervised`
- `ollama_exec`
- `ollama_exec_failed`
- `policy_denied`
- `project_lock_rejected`
- `router_all_failed`
- Dispatch rank tie-break contract (`RANK_TIE_BREAK_CONTRACT`):
- `score_desc`
- `agent_id_asc`
- `request_id_asc`

## Control Gate Snapshot (runtime-state source of truth)
- Generated at: `2026-02-19T18:03:13+00:00`
- Source paths:
- `runtime_state_path`: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/auto_mode_state.json`
- `requests_log_path`: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/requests.ndjson`
- `agents_state_glob`: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/*/state.json`
- Metrics:
- `pending_stale_gt24h`: `0` (ok)
- `queued_runtime_requests`: `15` (over gate `<=3`)
- `stale_heartbeats_gt1h`: `7` (over gate `<=2`)
- Drift visibility:
- `requests_log_open_like`: `9`
- `runtime_requests_count`: `39`

## Command Evidence
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_execution_router.py`
- Result: `OK: execution router verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave05_dispatch.py`
- Result: `OK: wave05 dispatch scoring/backpressure verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave05_router_fallback.py`
- Result: `OK: wave05 router fallback + cost + slo artifacts verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_cost_telemetry.py`
- Result: `OK: cost telemetry schema + monthly estimator verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode.py`
- Result: `OK: auto-mode runner verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_runtime_conformance_l2.py`
- Result: `OK: runtime conformance L2 verified`
- `python3 /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
- Result: `OK: wave07 control gate snapshot verified`

## Now
- Wave07 backend hardening contracts are locked and validated in tests.
- Queue gate now uses runtime-state latest statuses as source of truth.
- Telemetry and router error contracts are explicit and regression-tested.

## Next
- Keep status updates every 2h in Now/Next/Blockers.
- Run next gate recheck at `2026-02-19T2003Z` and publish delta.

## Blockers
- Runtime gate queue threshold is currently red: `queued_runtime_requests=15` (target `<=3`).
- Runtime stale heartbeat threshold is currently red: `stale_heartbeats_gt1h=7` (target `<=2`).
- Both blockers are tracked as ops/runtime cleanup outside this Wave07 backend hardening code lock.
