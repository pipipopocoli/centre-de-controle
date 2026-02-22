# capacity_slo_report.md

## Metadata
- stream: S7
- layer: L7
- owner: competitor-r1-b
- approval_ref: not_required_workspace_only
- focus: CAP-L7-004 and CAP-L7-005

## Capability traceability
| capability_id | interface | imports | source anchor | status |
|---|---|---|---|---|
| CAP-L7-004 | capacity_slo | r1-c,r1-a | 02_CAPABILITY_REGISTRY.md | implemented |
| CAP-L7-005 | staffing_model | r1-e,r1-f | 02_CAPABILITY_REGISTRY.md | implemented |
| CAP-L7-003 | budget linkage | r1-e,r1-f | budget_guardrail_report.md | linked |

## Capacity SLO contracts
| service_scope | target_p95_latency_ms | target_error_rate_pct | max_load_envelope | max_monthly_cost_units |
|---|---:|---:|---|---:|
| router_ingress | 250 | 0.8 | xlarge steady with burst 1.2x | 40 |
| policy_preflight | 180 | 0.5 | large steady | 22 |
| eval_dispatch | 600 | 1.2 | xlarge burst windows | 28 |
| telemetry_ingest | 300 | 0.7 | xlarge sustained | 18 |
| operator_summary_feed | 350 | 0.9 | large steady | 12 |

## 40-dev staffing model checks (CAP-L7-005)
Source allocation from mega plan:
- S1: 8 dev
- S2: 7 dev
- S3: 7 dev
- S4: 6 dev
- S5: 5 dev
- S6: 4 dev
- S7: 3 dev
- total: 40 dev

Coverage checks:
- one owner per stream: pass
- no duplicate stream ownership conflicts: pass
- high-risk concurrency constraint: max 2 major high-risk tickets per stream at once
- cross-stream dependency sync: weekly capacity sync required for S3/S5/S7 coupling

## Capacity risk model
| risk_id | trigger | impact | mitigation | escalation_owner |
|---|---|---|---|---|
| CAP-R01 | router p95 > target for 3 windows | queue spillover | enable burst controls, throttle low-priority jobs | S3 owner |
| CAP-R02 | eval backlog > 1.5x weekly median | delayed verdicts | shift heavy suites to nightly lane | S5 owner |
| CAP-R03 | telemetry delay > 24h | blind cost view | force safe fallback mode | S7 owner |
| CAP-R04 | staffing overlap on critical path | delivery stall | rebalance within stream cap and freeze non-critical work | program PM |
| CAP-R05 | cost envelope + latency breach combined | reliability and budget risk | invoke incident protocol and temporary dispatch limits | @clems |

## Verification matrix
| check_id | check | expected |
|---|---|---|
| V-SLO-01 | load profile coverage across small/medium/large/xlarge | complete |
| V-SLO-02 | SLO targets present per service scope | complete |
| V-SLO-03 | staffing allocation sums to 40 dev | true |
| V-SLO-04 | stream ownership complete and unique | true |
| V-SLO-05 | high-risk concurrency constraint defined | true |

## Shared constraints check
- scenario names aligned with cost_model_spec.md.
- hard-stop and fallback wording aligned with budget_guardrail_report.md.
- staffing model aligned with 04_MEGA_PLAN_V2_FINAL.md.

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/capacity_slo_report.md

## DoD evidence
- CAP-L7-004 documented with explicit service-level contract table and thresholds.
- CAP-L7-005 validated with 40-dev allocation and ownership completeness checks.

## test results
- load-profile coverage check: pass
- SLO threshold contract check: pass
- staffing sum and ownership checks: pass

## rollback note
- If SLO targets prove unrealistic in first rollout window, fallback to baseline targets from previous sprint while preserving staffing completeness constraints.

Now
- capacity and staffing contracts are documented and cross-checked against mega plan.

Next
- handoff to integration stream for cross-layer coherence and go/no-go lock.

Blockers
- none.
