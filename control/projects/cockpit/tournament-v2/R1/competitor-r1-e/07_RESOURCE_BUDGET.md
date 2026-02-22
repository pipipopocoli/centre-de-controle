# 07 - Resource Budget (Operating envelope)

## Context
Eval harness quality is only useful if it fits time and cost constraints for daily development at 40-dev scale.

## Problem statement
Unbounded benchmark execution causes slow merges, cost blow-ups, and team bypass behavior. We need explicit budgets and kill switches.

## Proposed design
Budget model is split across 5 dimensions:
1. Compute budget (CPU/GPU hours).
2. Token/API budget.
3. Storage budget.
4. Human operations budget.
5. Latency budget (developer wait time).

### Baseline monthly envelope
- Compute: 2,400 to 3,600 CPU-hours/month.
- Token/API spend: USD 9,000 to 16,000/month.
- Storage (artifacts + metrics): 300 to 450 GB/month raw, compacted to 120 to 200 GB/month.
- Human operations: 9 core FTE + 0.5 FTE per stream for scenario maintenance.
- Eval latency target: p50 <= 25 min, p95 <= 45 min.

### Guardrails
- If monthly token trend exceeds 80 percent of plan by day 20, automatically:
  - disable low-value stress variants,
  - reduce B2 sampling rate,
  - require manual approval for expanded suites.
- If p95 latency exceeds 45 min for 3 consecutive days:
  - increase shard count,
  - move heavy suites to nightly,
  - enforce stricter queue prioritization.

## Interfaces and contracts
- Budget contract (`budget_policy.yaml`):
  - thresholds, actions, owners, escalation path.
- Daily cost report contract:
  - per-suite cost, per-project cost, variance vs budget.
- Escalation contract:
  - cost breach > 15 percent triggers `@victor` review,
  - > 25 percent triggers `@clems` approval gate.

## Failure modes
- Hidden cost from retries and flake reruns.
- Storage growth from unbounded trace retention.
- Human overload during high-fail periods.

## Validation strategy
- Weekly budget variance review.
- Monthly what-if simulation on load spikes.
- Compare projected vs actual run mix.
- Track marginal value per benchmark suite.

## Rollout/rollback
- Start conservative with B0/B1 full, B2 sampled, B3 nightly only.
- Expand suites only after 2 weeks stable budget behavior.
- Rollback by reverting budget policy version and dropping optional suites.

## Risks and mitigations
- Risk: over-optimizing for cost lowers quality.
  - Mitigation: never relax critical hard-fail checks.
- Risk: budget noise masks regressions.
  - Mitigation: isolate cost metrics from quality verdict logic.
- Risk: sudden provider pricing shift.
  - Mitigation: monthly re-baseline and multi-provider abstraction.

## Resource impact
- Predictable spend supports operator trust.
- Runtime guardrails keep dev velocity stable.
- Added governance overhead is offset by fewer escaped defects.

## References
Key sources: [P1][P5][P8][R1][R2][R6][S2][S3], assumptions [A2][A4].
