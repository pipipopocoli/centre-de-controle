# router_contracts

## Context
This document implements Stream S3 L3 Router orchestration using the locked L3 capability set as the only design source.
Layer ownership stays locked to competitor-r1-c for scheduler and fallback orchestration.
No ad-hoc redesign is introduced outside capability registry scope.

Scope In
- Router front-door contracts.
- Weighted fair scheduling and starvation protection.
- Anti-thundering-herd controls.
- Fallback tier deterministic state machine.
- Provider adapter contracts.
- Dispatch budget envelopes and hard-stop rules.
- Trace correlation contract for run, dispatch, and fallback.

Scope Out
- Trust-tier governance internals owned by L2.
- Memory indexing and promotion internals owned by L4.
- Eval release policy internals owned by L5.

## Capability map
| capability_id | owner | imports | interface | test_gate |
|---|---|---|---|---|
| CAP-L3-001 | competitor-r1-c | r1-a,r1-b | RouterFrontDoorRequest, RouterFrontDoorDecision | request contract validation pass |
| CAP-L3-002 | competitor-r1-c | r1-b,r1-f | SchedulerDecisionRecord, FairnessInvariantSet | weighted fairness and starvation tests pass |
| CAP-L3-003 | competitor-r1-c | r1-a,r1-e | BurstControlPolicy, AdmissionDecision | anti-thundering-herd benchmark pass |
| CAP-L3-004 | competitor-r1-c | r1-a,r1-b | FallbackTransitionEvent, FallbackTierState | tiered fallback transitions deterministic |
| CAP-L3-005 | competitor-r1-c | r1-b,r1-e | ProviderAdapterRequest, ProviderAdapterResponse | adapter health and timeout gate pass |
| CAP-L3-006 | competitor-r1-c | r1-b,r1-f | DispatchBudgetEnvelope, BudgetGuardDecision | hard-stop budget guardrails enforced |
| CAP-L3-007 | competitor-r1-c | r1-a,r1-e | TraceCorrelationContract, TraceLineageRecord | end-to-end trace ids complete |

## Interfaces and contracts
### RouterFrontDoorRequest
- run_id: stable run identifier.
- project_id: project namespace id.
- requested_capability: target capability domain.
- priority: interactive or batch lane priority.
- budget_envelope: max tokens, max cost, max elapsed_ms.
- approval_ref: required for any full-access path.
- trace_context: parent trace id and span seed.

### RouterFrontDoorDecision
- decision: allow, deny, hold.
- queue_class: interactive or batch.
- provider_candidate_set: ranked provider ids.
- fallback_start_tier: T0 default unless degraded entry path.
- policy_flags: normalized policy outcomes imported from L2.
- replay_anchor: deterministic replay reference imported from L1.

### SchedulerDecisionRecord
- scheduler_tick_id.
- queue_depth_snapshot.
- fairness_credit_before.
- fairness_credit_after.
- selected_queue.
- selected_run_id.
- starvation_window_ms.
- starvation_guard_fired: bool.

### FairnessInvariantSet
- no queue starvation over configured window.
- interactive lane preempts batch only within max fairness skew.
- weighted shares converge over rolling horizon.
- dispatch without replay anchor is denied.

### BurstControlPolicy
- token_bucket_rate_per_queue.
- token_bucket_burst_per_queue.
- retry_jitter_min_ms.
- retry_jitter_max_ms.
- per_project_concurrency_cap.
- thundering_herd_trip_threshold.

### AdmissionDecision
- admit or reject.
- reject_reason: overload, budget_limit, policy_deny, provider_unhealthy.
- retry_after_ms when reject is transient.

### FallbackTierState
- T0: same provider bounded retry.
- T1: provider switch in same capability class.
- T2: safe mode degraded execution.
- T3: dispatch hold and operator escalation.

### FallbackTransitionEvent
- run_id.
- from_tier.
- to_tier.
- trigger.
- guard_result.
- action_applied.
- timeout_budget_remaining_ms.
- trace_event_id.

### ProviderAdapterRequest
- run_id.
- project_id.
- normalized_payload.
- policy_bundle_id.
- approval_ref if full-access.
- dispatch_deadline_ms.

### ProviderAdapterResponse
- status: ok, retryable_error, terminal_error, policy_error.
- provider_latency_ms.
- usage_metrics.
- error_class.
- adapter_health_snapshot.

### DispatchBudgetEnvelope
- max_input_tokens.
- max_output_tokens.
- max_total_tokens.
- max_cost_usd.
- max_elapsed_ms.
- hard_stop_enabled: true.

### BudgetGuardDecision
- allow_dispatch.
- projected_cost_usd.
- projected_tokens.
- hard_stop_triggered.
- escalation_required.

### TraceCorrelationContract
- trace_id.
- run_id.
- scheduler_tick_id.
- dispatch_attempt_id.
- fallback_transition_id.
- provider_call_id.
- replay_event_id.

### TraceLineageRecord
- parent_trace_id.
- current_trace_id.
- causal_link_type.
- timestamp_utc.

## Import boundaries
### L1 boundary
- L3 consumes deterministic replay anchor and run bundle boundary from L1.
- L3 does not redefine event integrity semantics or replay hash policy.

### L2 boundary
- L3 consumes policy conformance outputs and approval_ref gate outcomes from L2.
- L3 must deny full-access dispatch when approval_ref is missing or invalid.

## Hard constraint notes
- cross-project retrieval is denied in router paths.
- full-access dispatch requires approval_ref at intake and adapter boundaries.
- approval_ref must be propagated through all retries and fallback tiers.

## Failure modes
- FM-L3-01: fairness drift causes hidden starvation.
- FM-L3-02: burst storm bypasses token bucket guard.
- FM-L3-03: stale provider health drives wrong fallback tier.
- FM-L3-04: missing replay anchor causes non-deterministic recovery.
- FM-L3-05: budget envelope ignored during retry fanout.
- FM-L3-06: trace break between dispatch and fallback events.

## Validation strategy
- Contract schema validation for all request and decision objects.
- Fairness soak scenarios with deterministic seed.
- Burst storm scenario with controlled arrival profile.
- Adapter timeout and health gate tests.
- Budget hard-stop simulation with projected and actual drift checks.
- Trace continuity checks across retry and fallback paths.

## Rollout/rollback
- Stage A: front-door contract and trace emission in observe mode.
- Stage B: scheduler fairness and burst controls in soft enforcement.
- Stage C: fallback tiers and budget hard-stop in hard enforcement.
- Rollback 1: force safe scheduler mode and disable dynamic weighting.
- Rollback 2: lock fallback at T3 hold for unstable provider windows.
- Rollback 3: disable optional adapter branches and keep primary providers only.

## Risks and mitigations
- Risk: high scheduler complexity slows operator triage.
  - Mitigation: deterministic event model and explicit decision fields.
- Risk: policy drift between providers.
  - Mitigation: adapter contract parity checks from L2 imports.
- Risk: spend spike during retries.
  - Mitigation: strict budget envelope with hard-stop and escalation.
- Risk: trace gaps reduce audit confidence.
  - Mitigation: required trace lineage fields at every transition point.

## Resource impact
- Team split for S3 execution package:
  - scheduler and fairness: 3 dev.
  - adapter and fallback contract hardening: 2 dev.
  - benchmarking and trace validation: 2 dev.
- Runtime cost profile:
  - moderate CI load for soak and burst tests.
  - bounded replay and trace storage growth via retention policies.

changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/router_contracts.md

DoD evidence
- Capability map covers the full locked L3 capability set with owner/import/interface/test_gate.
- Router contract includes explicit L1 and L2 import boundaries.
- Hard constraints include cross-project denial and approval_ref requirement.

test results
- Contract lint: pass.
- Scope lock check: pass.
- Hard constraint token visibility: pass.

rollback note
- If any contract ambiguity appears during integration lock, freeze S3 rollout at Stage A and revert to previous locked capability mapping until mismatch is resolved.

Now
- stream packet updated and aligned with integration contract.

Next
- maintain coherence with cross-layer integration lock checks.

Blockers
- none.
