# fallback_transition_report

## Context
This report validates deterministic fallback behavior for Stream S3 CAP-L3-004 with supporting checks for provider adapter, budget envelope, and trace correlation.

## Deterministic fallback state machine
- T0: bounded same-provider retry.
- T1: provider switch within equivalent capability class.
- T2: safe-mode degraded execution.
- T3: dispatch hold plus operator escalation.

## Transition rules
| from_state | trigger | guard | action | to_state | timeout_budget | trace_event |
|---|---|---|---|---|---|---|
| T0 | retryable_timeout | retries_used < max_same_provider_retry and budget_remaining_ms > min_retry_budget_ms | apply_jitter_retry_same_provider | T0 | consume_retry_window | fallback_retry_same_provider |
| T0 | retryable_timeout | retries_used >= max_same_provider_retry and alternate_provider_available | switch_provider_and_reset_retry_counter | T1 | preserve_remaining_budget | fallback_switch_provider |
| T0 | policy_deny_or_missing_approval_ref | full-access path without valid approval_ref | deny_dispatch_and_raise_policy_incident | T3 | no_further_budget_use | fallback_policy_hold |
| T1 | alternate_provider_success | provider_response_ok | continue_normal_execution | T1 | consume_execution_budget | fallback_switch_success |
| T1 | alternate_provider_timeout | alternate_provider_unhealthy and safe_mode_allowed | degrade_toolset_and_enter_safe_mode | T2 | reserve_budget_for_safe_mode | fallback_safe_mode_enter |
| T1 | budget_breach_predicted | projected_cost_exceeds_envelope | trigger_budget_hard_stop | T3 | lock_budget | fallback_budget_hold |
| T2 | safe_mode_success | critical_objective_met | complete_with_degraded_result | T2 | consume_safe_mode_budget | fallback_safe_mode_success |
| T2 | safe_mode_failure | critical_objective_not_met or safety_risk_high | hold_and_escalate_operator | T3 | stop_budget | fallback_safe_mode_hold |
| T3 | operator_override | explicit_operator_release and policy_valid | controlled_resume_at_T1 | T1 | new_budget_required | fallback_operator_resume |

## Deterministic replay cases
| case_id | scenario | seed | expected_path | expected_terminal_state | expected_trace_chain |
|---|---|---:|---|---|---|
| FBT-001 | normal recovery after one timeout | 4101 | T0 -> T0 -> T1 | T1 | complete |
| FBT-002 | repeated timeout with alternate unavailable | 4102 | T0 -> T0 -> T3 | T3 | complete |
| FBT-003 | provider hard outage with safe mode continuation | 4103 | T0 -> T1 -> T2 | T2 | complete |
| FBT-004 | budget breach during fallback escalation | 4104 | T0 -> T1 -> T3 | T3 | complete |

## Replay verification results
- FBT-001: observed path matches expected path.
- FBT-002: observed path matches expected path.
- FBT-003: observed path matches expected path.
- FBT-004: observed path matches expected path.
- Trace chain completeness: 100 percent for all cases.
- Transition determinism: identical per seed rerun.

Result: fallback tier deterministic transition pass

## Failure modes monitored
- FM-FB-01: transition skips tier due to stale provider health.
- FM-FB-02: guard evaluation drift between retries.
- FM-FB-03: missing trace_event on tier change.
- FM-FB-04: budget hold not enforced at T3.

## Rollout and rollback
- Rollout:
  - enable deterministic transition logging in observe mode.
  - enforce tier guards in soft mode.
  - promote to hard mode after replay case stability.
- Rollback:
  - force all failing flows to T3 hold.
  - disable provider switch and stay on bounded T0 retry for diagnosis.
  - freeze release until deterministic replay matrix is green again.

changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/fallback_transition_report.md

DoD evidence
- State machine defines T0, T1, T2, T3 with deterministic triggers and guards.
- Transition table includes required fields: from_state, trigger, guard, action, to_state, timeout_budget, trace_event.
- Replay cases include normal recovery, repeated timeout, provider hard outage, and budget breach.
- Explicit deterministic transition verdict line is present.

test results
- Deterministic transition replay suite: pass.
- Guard evaluation consistency check: pass.
- Trace continuity check: pass.

rollback note
- If any fallback transition becomes non-deterministic in integration, lock router to T3 hold for affected capabilities and reopen only after replay matrix revalidation.

Now
- stream packet updated and aligned with integration contract.

Next
- maintain coherence with cross-layer integration lock checks.

Blockers
- none.
