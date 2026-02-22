# 02_CAPABILITY_REGISTRY

## Contract
Each row is one and only one architecture capability.
No duplicate owner per capability.

Fields:
- capability_id
- layer
- owner
- imports
- status
- interfaces_impacted
- test_gate

## Registry

| capability_id | layer | owner | imports | status | interfaces_impacted | test_gate |
|---|---|---|---|---|---|---|
| CAP-L1-001 | L1 | competitor-r1-a | r1-b,r1-c | locked | run_bundle | replay hash stable across 10 replays |
| CAP-L1-002 | L1 | competitor-r1-a | r1-c,r1-d | locked | event_log_store | append-only invariants pass |
| CAP-L1-003 | L1 | competitor-r1-a | r1-b,r1-e | locked | transaction_boundary | duplicate write test shows idempotent behavior |
| CAP-L1-004 | L1 | competitor-r1-a | r1-c,r1-e | locked | retry_state_machine | timeout/retry chaos scenario pass |
| CAP-L1-005 | L1 | competitor-r1-a | r1-b,r1-d | locked | wal_integrity | checksum corruption quarantine works |
| CAP-L1-006 | L1 | competitor-r1-a | r1-c,r1-e | locked | recovery_cli | crash injection recovery pass |
| CAP-L2-001 | L2 | competitor-r1-b | r1-f,r1-e | locked | skills_lock_schema | lockfile lint and signature validation pass |
| CAP-L2-002 | L2 | competitor-r1-b | r1-e,r1-f | locked | trust_tier_policy | tier upgrade policy tests pass |
| CAP-L2-003 | L2 | competitor-r1-b | r1-a,r1-e | locked | provenance_contract | forged provenance test denied |
| CAP-L2-004 | L2 | competitor-r1-b | r1-f,r1-c | locked | skill_lifecycle | install/update/revoke transitions verified |
| CAP-L2-005 | L2 | competitor-r1-b | r1-a,r1-f | locked | approval_policy | no full-access action without approval_ref |
| CAP-L2-006 | L2 | competitor-r1-b | r1-e,r1-c | locked | revoke_pipeline | compromised skill quarantine in SLA |
| CAP-L2-007 | L2 | competitor-r1-b | r1-c,r1-e | locked | runtime_conformance | codex vs antigravity policy parity pass |
| CAP-L3-001 | L3 | competitor-r1-c | r1-a,r1-b | locked | router_frontdoor | request contract validation pass |
| CAP-L3-002 | L3 | competitor-r1-c | r1-b,r1-f | locked | scheduler_core | weighted fairness and starvation tests pass |
| CAP-L3-003 | L3 | competitor-r1-c | r1-a,r1-e | locked | burst_control | anti-thundering-herd benchmark pass |
| CAP-L3-004 | L3 | competitor-r1-c | r1-a,r1-b | locked | fallback_policy | tiered fallback transitions deterministic |
| CAP-L3-005 | L3 | competitor-r1-c | r1-b,r1-e | locked | provider_adapter | adapter health and timeout gate pass |
| CAP-L3-006 | L3 | competitor-r1-c | r1-b,r1-f | locked | budget_envelope | hard-stop budget guardrails enforced |
| CAP-L3-007 | L3 | competitor-r1-c | r1-a,r1-e | locked | trace_correlation | end-to-end trace ids complete |
| CAP-L4-001 | L4 | competitor-r1-d | r1-a,r1-e | locked | memory_namespace | cross-project read denied in tests |
| CAP-L4-002 | L4 | competitor-r1-d | r1-a,r1-f | locked | fts_retrieval | p95 lexical query threshold pass |
| CAP-L4-003 | L4 | competitor-r1-d | r1-e,r1-c | locked | semantic_lane | semantic path remains gated by policy |
| CAP-L4-004 | L4 | competitor-r1-d | r1-a,r1-e | locked | compaction_retention | compaction reduction and restore tests pass |
| CAP-L4-005 | L4 | competitor-r1-d | r1-b,r1-f | locked | promotion_gate | global promotion requires clems approval |
| CAP-L4-006 | L4 | competitor-r1-d | r1-e,r1-a | locked | contamination_guard | sentinel contamination tests pass |
| CAP-L5-001 | L5 | competitor-r1-e | r1-c,r1-b | locked | scenario_registry | benchmark catalog versioning pass |
| CAP-L5-002 | L5 | competitor-r1-e | r1-a,r1-c | locked | replay_schema | replay bundle schema validation pass |
| CAP-L5-003 | L5 | competitor-r1-e | r1-b,r1-f | locked | metrics_schema | gate threshold parser and validation pass |
| CAP-L5-004 | L5 | competitor-r1-e | r1-c,r1-b | locked | calibration_model | fp/fn confusion matrix target pass |
| CAP-L5-005 | L5 | competitor-r1-e | r1-f,r1-b | locked | release_policy | pass/soft_fail/hard_fail policy applied |
| CAP-L5-006 | L5 | competitor-r1-e | r1-b,r1-f | locked | override_audit | override requires approval + rationale |
| CAP-L6-001 | L6 | competitor-r1-f | r1-e,r1-c | locked | summary_cards | 60-second comprehension test pass |
| CAP-L6-002 | L6 | competitor-r1-f | r1-e,r1-a | locked | pressure_mode | critical mode card ordering verified |
| CAP-L6-003 | L6 | competitor-r1-f | r1-c,r1-e | locked | freshness_contract | stale warn/critical thresholds correct |
| CAP-L6-004 | L6 | competitor-r1-f | r1-e,r1-b | locked | evidence_links | evidence links resolve and open |
| CAP-L6-005 | L6 | competitor-r1-f | r1-c,r1-e | locked | accessibility_contract | keyboard and fallback table pass |
| CAP-L6-006 | L6 | competitor-r1-f | r1-e,r1-a | locked | comprehension_gate | >=85 percent answer accuracy in drill |
| CAP-L7-001 | L7 | competitor-r1-b | r1-c,r1-f | locked | cost_event_schema | telemetry event schema validation pass |
| CAP-L7-002 | L7 | competitor-r1-b | r1-c,r1-e | locked | scenario_model | small/medium/large/xlarge values complete |
| CAP-L7-003 | L7 | competitor-r1-b | r1-e,r1-f | locked | budget_alerts | budget alert SLA and routing pass |
| CAP-L7-004 | L7 | competitor-r1-b | r1-c,r1-a | locked | capacity_slo | load and latency targets documented and tested |
| CAP-L7-005 | L7 | competitor-r1-b | r1-e,r1-f | locked | staffing_model | 40-dev stream ownership complete |
| CAP-L7-006 | L7 | competitor-r1-b | r1-c,r1-f | locked | breakeven_matrix | subscription vs API comparison reproducible |

## Notes
- `r1-a` means competitor-r1-a, same pattern for all imports.
- Status `locked` means no unresolved design decision remains for this capability.
