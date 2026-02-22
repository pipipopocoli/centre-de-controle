# integration_lock_report

## Control context
- project_lock: cockpit
- evidence_root: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE
- timestamp_utc: 2026-02-18T21:24:57Z
- operator_mode: strict
- allowed_sources:
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/01_LAYER_OWNERSHIP_MATRIX.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/02_CAPABILITY_REGISTRY.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/03_CONFLICT_RESOLUTION_LOG.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/05_IMPLEMENTATION_PROMPT_PACK.md

## Executive verdict
- Overall integration lock: FAIL
- Final release decision: NO-GO

| check_id | check_name | result | blocking | evidence |
|---|---|---|---|---|
| A | ownership_uniqueness | PASS | no | rows=44, unique_capability_ids=44, duplicate_capability_ids=0 |
| B | interface_coherence | PASS | no | canonical_domains=7, owner_mismatch=0, duplicate_interfaces_impacted=0 |
| C | gates_executable | FAIL | yes | invalid_rows=0, missing_stream_artifacts=3 |
| D | conflict_closure | PASS | no | resolved_conflicts=22, deferred_items=3, unresolved_without_owner=0 |

## Missing artifacts (if any)
- router_contracts.md
- scheduler_benchmark_report.md
- fallback_transition_report.md

## Artifact ledger
| artifact | stream | owner | exists | changed_artifacts | dod_evidence | test_results | rollback_note | status |
|---|---|---|---|---|---|---|---|---|
| `reliability_contract.md` | S1 | @agent-1 | yes | yes | yes | yes | yes | PASS |
| `replay_validation_report.md` | S1 | @agent-1 | yes | yes | yes | yes | yes | PASS |
| `crash_recovery_test_report.md` | S1 | @agent-1 | yes | yes | yes | yes | yes | PASS |
| `skills_policy_spec.md` | S2 | @agent-2 | yes | yes | yes | yes | yes | PASS |
| `conformance_test_report.md` | S2 | @agent-2 | yes | yes | yes | yes | yes | PASS |
| `revoke_drill_report.md` | S2 | @agent-2 | yes | yes | yes | yes | yes | PASS |
| `router_contracts.md` | S3 | @agent-3 | yes | no | no | no | no | FAIL |
| `scheduler_benchmark_report.md` | S3 | @agent-3 | yes | no | no | no | no | FAIL |
| `fallback_transition_report.md` | S3 | @agent-3 | yes | no | no | no | no | FAIL |
| `memory_contracts.md` | S4 | @agent-4 | yes | yes | yes | yes | yes | PASS |
| `isolation_test_report.md` | S4 | @agent-4 | yes | yes | yes | yes | yes | PASS |
| `compaction_restore_report.md` | S4 | @agent-4 | yes | yes | yes | yes | yes | PASS |
| `eval_contracts.md` | S5 | @agent-5 | yes | yes | yes | yes | yes | PASS |
| `threshold_validation_report.md` | S5 | @agent-5 | yes | yes | yes | yes | yes | PASS |
| `calibration_report.md` | S5 | @agent-5 | yes | yes | yes | yes | yes | PASS |
| `vulgarisation_ui_spec.md` | S6 | @agent-6 | yes | yes | yes | yes | yes | PASS |
| `comprehension_test_report.md` | S6 | @agent-6 | yes | yes | yes | yes | yes | PASS |
| `accessibility_report.md` | S6 | @agent-6 | yes | yes | yes | yes | yes | PASS |
| `cost_model_spec.md` | S7 | @agent-7 | yes | yes | yes | yes | yes | PASS |
| `budget_guardrail_report.md` | S7 | @agent-7 | yes | yes | yes | yes | yes | PASS |
| `capacity_slo_report.md` | S7 | @agent-7 | yes | yes | yes | yes | yes | PASS |
| `integration_lock_report.md` | Integration | @agent-8 | yes | yes | yes | yes | yes | PASS |
| `final_go_no_go.md` | Integration | @agent-8 | yes | yes | yes | yes | yes | PASS |

## Interface coherence matrix
| layer | owner_from_matrix | owner_from_registry | capability_count | status |
|---|---|---|---|---|
| L1 | competitor-r1-a | competitor-r1-a | 6 | PASS |
| L2 | competitor-r1-b | competitor-r1-b | 7 | PASS |
| L3 | competitor-r1-c | competitor-r1-c | 7 | PASS |
| L4 | competitor-r1-d | competitor-r1-d | 6 | PASS |
| L5 | competitor-r1-e | competitor-r1-e | 6 | PASS |
| L6 | competitor-r1-f | competitor-r1-f | 6 | PASS |
| L7 | competitor-r1-b | competitor-r1-b | 6 | PASS |

## Gate mapping
| capability_id | layer | test_gate | required_evidence_files |
|---|---|---|---|
| `CAP-L1-001` | L1 | replay hash stable across 10 replays | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L1-002` | L1 | append-only invariants pass | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L1-003` | L1 | duplicate write test shows idempotent behavior | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L1-004` | L1 | timeout/retry chaos scenario pass | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L1-005` | L1 | checksum corruption quarantine works | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L1-006` | L1 | crash injection recovery pass | `reliability_contract.md, replay_validation_report.md, crash_recovery_test_report.md` |
| `CAP-L2-001` | L2 | lockfile lint and signature validation pass | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-002` | L2 | tier upgrade policy tests pass | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-003` | L2 | forged provenance test denied | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-004` | L2 | install/update/revoke transitions verified | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-005` | L2 | no full-access action without approval_ref | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-006` | L2 | compromised skill quarantine in SLA | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L2-007` | L2 | codex vs antigravity policy parity pass | `skills_policy_spec.md, conformance_test_report.md, revoke_drill_report.md` |
| `CAP-L3-001` | L3 | request contract validation pass | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-002` | L3 | weighted fairness and starvation tests pass | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-003` | L3 | anti-thundering-herd benchmark pass | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-004` | L3 | tiered fallback transitions deterministic | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-005` | L3 | adapter health and timeout gate pass | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-006` | L3 | hard-stop budget guardrails enforced | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L3-007` | L3 | end-to-end trace ids complete | `router_contracts.md, scheduler_benchmark_report.md, fallback_transition_report.md` |
| `CAP-L4-001` | L4 | cross-project read denied in tests | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L4-002` | L4 | p95 lexical query threshold pass | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L4-003` | L4 | semantic path remains gated by policy | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L4-004` | L4 | compaction reduction and restore tests pass | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L4-005` | L4 | global promotion requires clems approval | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L4-006` | L4 | sentinel contamination tests pass | `memory_contracts.md, isolation_test_report.md, compaction_restore_report.md` |
| `CAP-L5-001` | L5 | benchmark catalog versioning pass | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L5-002` | L5 | replay bundle schema validation pass | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L5-003` | L5 | gate threshold parser and validation pass | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L5-004` | L5 | fp/fn confusion matrix target pass | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L5-005` | L5 | pass/soft_fail/hard_fail policy applied | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L5-006` | L5 | override requires approval + rationale | `eval_contracts.md, threshold_validation_report.md, calibration_report.md` |
| `CAP-L6-001` | L6 | 60-second comprehension test pass | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L6-002` | L6 | critical mode card ordering verified | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L6-003` | L6 | stale warn/critical thresholds correct | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L6-004` | L6 | evidence links resolve and open | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L6-005` | L6 | keyboard and fallback table pass | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L6-006` | L6 | >=85 percent answer accuracy in drill | `vulgarisation_ui_spec.md, comprehension_test_report.md, accessibility_report.md` |
| `CAP-L7-001` | L7 | telemetry event schema validation pass | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |
| `CAP-L7-002` | L7 | small/medium/large/xlarge values complete | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |
| `CAP-L7-003` | L7 | budget alert SLA and routing pass | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |
| `CAP-L7-004` | L7 | load and latency targets documented and tested | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |
| `CAP-L7-005` | L7 | 40-dev stream ownership complete | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |
| `CAP-L7-006` | L7 | subscription vs API comparison reproducible | `cost_model_spec.md, budget_guardrail_report.md, capacity_slo_report.md` |

## Conflict audit
- total_conflicts_logged: 25
- resolved_conflicts: 22
- deferred_items: 3
- unresolved_without_owner: 0

## Rollback map by layer
- L1: rollback on replay hash drift or crash-recovery gate failure.
- L2: rollback on approval gate bypass or policy parity failure.
- L3: rollback on starvation regression or non-deterministic fallback.
- L4: rollback on contamination sentinel hit or promotion gate bypass.
- L5: rollback on verdict policy mismatch or override audit gaps.
- L6: rollback on comprehension gate failure or stale threshold mismatch.
- L7: rollback on hard-stop budget rule failure or non-reproducible breakeven matrix.

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/integration_lock_report.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/final_go_no_go.md

## DoD evidence
- Checks A/B/C/D executed from locked sources.
- Artifact ledger enforces strict section contract checks.
- Overall result: FAIL, verdict: NO-GO.

## test results
- capability rows parsed: 44
- invalid capability rows: 0
- missing_stream_artifacts: 3
- check_A: PASS
- check_B: PASS
- check_C: FAIL
- check_D: PASS

## rollback note
- Re-run this script with corrected artifacts.
- Reports are regenerated deterministically from source files and current artifact state.

## Now / Next / Blockers
- Now: strict lock refresh complete with verdict `NO-GO`.
- Next: rerun lock checks after any stream artifact update.
- Blockers: none.
