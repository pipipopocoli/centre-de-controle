# budget_guardrail_report.md

## Metadata
- stream: S7
- layer: L7
- owner: competitor-r1-b
- approval_ref: not_required_workspace_only
- focus: CAP-L7-003 hard-stop budget policy and alert routing

## Capability traceability
| capability_id | interface | imports | source anchor | status |
|---|---|---|---|---|
| CAP-L7-003 | budget_alerts | r1-e,r1-f | 02_CAPABILITY_REGISTRY.md | implemented |
| CAP-L7-006 | breakeven_matrix link | r1-c,r1-f | cost_model_spec.md | linked |

## Guardrail policy
### Thresholds
- warn_threshold_pct_of_monthly_cap = 80
- critical_threshold_pct_of_monthly_cap = 95
- hard_stop_threshold_pct_of_monthly_cap = 100

### Consecutive breach behavior
- Rule B1: if `critical` for 2 consecutive daily windows -> auto route to owner + escalation owner.
- Rule B2: if `hard-stop` reached in any window -> immediate stop action on non-critical runs.
- Rule B3: if stale telemetry > 24h -> safe fallback mode and manual approval required to resume expansions.

### Cap references
- monthly_cap_cad is scenario-bounded from `cost_model_spec.md`.
- run_cap_cad is derived per scenario and enforced at ingress.
- per_project_cap_cad prevents one project from consuming >40% of monthly cap.

## Alert routing and SLA
| alert_level | primary_owner | escalation_owner | max_time_to_ack | route |
|---|---|---|---|---|
| warn | stream-s7-owner | program-pm | 4h | async dashboard + digest |
| critical | stream-s7-owner | @victor | 1h | direct page + issue ticket |
| hard-stop | stream-s7-owner | @clems | 15m | blocking gate + incident room |

## Hard-stop policy contract
Fields:
- alert_id
- trigger
- threshold_value
- observed_value
- stop_action
- scope
- owner
- escalation_owner
- release_override_policy

Stop action semantics:
- stop_action=`halt_non_critical_dispatch`
- scope=`new runs only` (in-flight runs continue with audit tag)
- resume requires `clems_override_ref` when in hard-stop state

Release override rule:
- Hard-stop override requires explicit `@clems` approval reference and rationale.

## Test drill matrix
| drill_id | mode | setup | expected behavior | result |
|---|---|---|---|---|
| DRILL-S7-01 | normal | spend at 65% cap | no blocking, no escalation | pass |
| DRILL-S7-02 | warning | spend at 82% cap | warning routed, no stop action | pass |
| DRILL-S7-03 | critical consecutive | 96% cap for 2 windows | escalates to @victor and incident prep | pass |
| DRILL-S7-04 | breach hard-stop | 101% cap | hard-stop rule triggers, non-critical dispatch halted | pass |
| DRILL-S7-05 | stale telemetry | no events for 30h | safe fallback mode and manual approval lock | pass |

## Hard-stop budget rule tested
- Evidence summary:
  - DRILL-S7-04 explicitly reached hard-stop threshold and triggered stop action as specified.
  - DRILL-S7-05 validated safe fallback path under telemetry loss.
- Outcome:
  - done target `hard-stop budget rule tested` = pass.

## Shared constraints check
- hard-stop wording aligned with CR-019 decision (`adopt hard-stop`).
- routing aligns with L7 canonical ownership and L5/L6 imports.
- scenario naming remains aligned with cost_model_spec.md.

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/budget_guardrail_report.md

## DoD evidence
- CAP-L7-003 fully mapped to policy, routing, SLA, and drill evidence.
- hard-stop and stale telemetry fallback are explicitly exercised in drills.

## test results
- warning path: pass
- critical consecutive path: pass
- hard-stop breach path: pass
- stale telemetry safe fallback: pass

## rollback note
- If false positives occur, temporary rollback sets hard-stop to warning-only for 24h while preserving telemetry capture and escalation logs.

Now
- budget guardrail policy and alert routing finalized with tested hard-stop path.

Next
- complete capacity SLO and staffing completeness checks.

Blockers
- none.
