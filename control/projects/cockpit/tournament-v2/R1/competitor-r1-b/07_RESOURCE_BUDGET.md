# 07_RESOURCE_BUDGET - Operating Envelope And Cost Model

## Context
Variant B introduces additional control-plane and verification costs. This document defines a testable resource budget for team, infrastructure, API/token consumption, and operational support.

## Problem statement
Without explicit resource constraints, supply-chain security plans tend to fail in one of two ways:
- Underfunded controls that are bypassed in practice.
- Overbuilt controls that break velocity and exceed budget.

Cockpit V2 needs a budget model that preserves integrity while staying operable.

## Proposed design
### A. Budget dimensions
1. People budget
- 40 developers across six workstreams.
- Additional shared roles: 1 program director, 2 PMs, 2 security ops, 2 SRE on-call, 1 compliance lead.

2. Compute budget
- Control plane services (registry, policy, verifier): medium steady load.
- Eval harness and replay jobs: bursty high load.
- Storage: high for replay bundles and audit trails.

3. API/token budget
- Runtime preflight and policy calls per skill execution.
- Harness scenario expansions and replay validations.
- Operator workflows and audit report generation.

4. Risk reserve
- 15 percent engineering contingency.
- 20 percent incident/forensics reserve for first two quarters.

### B. Baseline monthly envelope (planning numbers)
- Engineering payroll + overhead: 100 units (relative baseline).
- Infrastructure:
  - Metadata and policy services: 10 units.
  - Replay/audit storage: 12 units.
  - Harness compute: 8 units.
- API/tokens:
  - Runtime operations: 6 units.
  - Eval/replay/testing: 5 units.
- Security tooling and scans: 4 units.
- Total baseline: 145 units.

ASSUMPTION (A5): Replay retention 30-day hot + 180-day cold fits within storage envelope.

### C. Stress envelope (incident quarter)
- Additional incident forensics and revoke activity:
  - +30 percent harness compute.
  - +25 percent storage growth.
  - +20 percent on-call staffing load.
- Stress total estimate: 165 to 178 units.

### D. Cost guardrails
- Guardrail G1: if monthly total > 160 units for 2 consecutive months, trigger scope review.
- Guardrail G2: if replay storage grows > 15 percent month-over-month, enforce compaction policy.
- Guardrail G3: if policy call latency optimization requires > 10 percent extra cost, require architecture review.

## Interfaces and contracts
### Contract: `BudgetSnapshot`
Fields:
- `month`
- `people_units`
- `infra_units`
- `api_units`
- `security_units`
- `total_units`
- `variance_vs_plan`

### Contract: `CapacitySLO`
Fields:
- `service_name`
- `target_p95_latency_ms`
- `target_error_rate`
- `max_monthly_cost_units`

### Contract: `BudgetAlert`
Fields:
- `alert_id`
- `trigger`
- `current_value`
- `owner_role`
- `mitigation_due_date`

### Contract: `RetentionProfile`
Fields:
- `profile_id`
- `hot_days`
- `cold_days`
- `compression_mode`
- `estimated_monthly_units`

## Failure modes
- FM1: Underestimated storage for replay bundles.
  - Mitigation: tiered retention and compression policy.

- FM2: Harness compute spikes during release windows.
  - Mitigation: reserved capacity and staggered runs.

- FM3: API/token runaway from repeated retries.
  - Mitigation: retry budgets and circuit breakers.

- FM4: On-call burnout under incident load.
  - Mitigation: rotation policy and staffing reserve.

- FM5: Cost dashboard lag hides overruns.
  - Mitigation: daily ingestion and automated alerts.

## Validation strategy
- Monthly budget variance report with workstream attribution.
- Weekly infra and token spend dashboard review.
- Quarterly stress test to validate reserve assumptions.
- Pre-release check: projected post-release cost must remain under approved envelope.

Validation thresholds:
- Monthly variance vs plan within +/- 10 percent.
- No unresolved critical budget alerts older than 7 days.

## Rollout/rollback
Rollout:
1. Instrument budget telemetry before hard enforcement.
2. Enable guardrail alerts in warning mode.
3. Move alerts to blocking gates for major releases.

Rollback:
- If metrics quality is poor, revert alerts to warning-only until data quality restored.
- Keep core spend tracking mandatory even in degraded mode.

## Risks and mitigations
- Risk: Relative-unit model not understood by all teams.
  - Mitigation: publish mapping guide to absolute budget.

- Risk: Hidden cross-team costs.
  - Mitigation: tag all spending by workstream and owner role.

- Risk: Budget pressure leads to security control weakening.
  - Mitigation: classify integrity controls as non-negotiable baseline.

- Risk: Overuse of emergency incident paths.
  - Mitigation: incident retros with prevention tickets.

- Risk: Forecast errors on API pricing or volume.
  - Mitigation: monthly reforecast and scenario planning.

## Resource impact
- Financial:
  - Baseline 145 units monthly with controlled variance.
- Human:
  - 40-dev sustained effort plus support roles.
- Technical:
  - Significant storage and harness compute allocation.
- Governance:
  - Regular budget reviews become part of release gate process.
