# Assumptions Register

Context
- Explicitly lists assumptions used in this R1 plan.

Problem statement
- Some execution details are project-specific and not fully specified in source docs.

Proposed design
- Every assumption is tagged and has a validation plan.

Interfaces and contracts
- Fields:
  - assumption_id
  - statement
  - risk_if_wrong
  - validation_plan
  - owner
  - due

Failure modes
- Untracked assumptions silently become design truth.

Validation strategy
- Assumptions reviewed at each milestone gate.

Rollout/rollback
- Rollout: keep assumptions as temporary gates.
- Rollback: replace or de-scope if invalidated.

Risks and mitigations
- Risk: too many assumptions lowers confidence.
- Mitigation: cap unresolved assumptions per phase and force closure.

Resource impact
- Low.

## Assumptions
- ASSUMPTION-A1 | @clems can process approval packets within one business day | risk_if_wrong: queue stalls and promotion lag | validation_plan: measure approval SLA on first 20 packets | owner: clems | due: Milestone M2.
- ASSUMPTION-A2 | Monthly API budget cap can be enforced at router layer without provider-native hard limit | risk_if_wrong: budget overrun | validation_plan: budget kill-switch simulation with synthetic load | owner: victor | due: M1.
- ASSUMPTION-A3 | Two-tier queue is sufficient before introducing third priority lane | risk_if_wrong: starvation under mixed load | validation_plan: soak test with adversarial workload | owner: victor | due: M2.
- ASSUMPTION-A4 | Optional provider abstraction can remain disabled by default in V2 without reducing operator value | risk_if_wrong: underutilized feature roadmap | validation_plan: operator interviews and incident replay usefulness score | owner: leo | due: M3.
- ASSUMPTION-A5 | Replay bundle storage growth remains manageable with 30-day retention | risk_if_wrong: storage cost spike | validation_plan: retention simulation on 90-day synthetic traces | owner: victor | due: M2.
- ASSUMPTION-A6 | Worker ephemeral model scales to 40-dev execution without identity conflicts | risk_if_wrong: ownership ambiguity | validation_plan: identity collision tests in harness | owner: clems | due: M1.
- ASSUMPTION-A7 | Anti-thundering-herd jitter of 50-250ms is enough for first release | risk_if_wrong: burst collapse remains | validation_plan: burst benchmark with tunable jitter windows | owner: victor | due: M1.
- ASSUMPTION-A8 | Existing project state files can provide enough signal for vulgarisation without extra ingestion | risk_if_wrong: stale or missing dashboard data | validation_plan: dry-run on 5 projects and freshness SLA check | owner: leo | due: M3.
