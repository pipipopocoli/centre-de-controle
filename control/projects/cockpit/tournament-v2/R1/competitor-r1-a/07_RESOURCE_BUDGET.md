# 07_RESOURCE_BUDGET

## Context
The operating envelope must be explicit: team capacity, runtime cost, token/API profile, and storage growth under stability-first constraints.

## Problem statement
Plans fail when cost assumptions are implicit. We need budget limits and testable operating ranges.

## Proposed design
Budget dimensions:
- People
- Time
- Compute
- Storage
- Token/API spend
- Reliability reserve

### People budget
- 40 dev total.
- 10 percent program management and coordination.
- 25 percent reliability reserve during phases 2-4.

### Time budget
- 16 weeks total.
- 4 milestone gates.
- hard freeze windows at each phase gate.

### Compute/storage budget
- persistent event logs and snapshots increase storage footprint.
- projected active storage growth: moderate-high during dual write.
- compaction should reduce warm tier growth after phase 3.

### API/token budget
ASSUMPTION-A1: baseline subscription can handle workspace-only skill execution volume.
- Validation plan: run one-week workload simulation and compare to quota telemetry.

ASSUMPTION-A2: replay verification can run mostly off cached artifacts.
- Validation plan: measure cache hit ratio in pilot and tune fixture locality.

## Interfaces and contracts
Budget contract:
- `budget_id`
- `period`
- `category`
- `planned`
- `actual`
- `variance`
- `owner`
- `action_threshold`

Variance policy:
- 0-10 percent: monitor.
- 10-20 percent: corrective action required.
- over 20 percent: gate escalation to @clems.

## Failure modes
- FM1: storage overrun from replay artifacts.
  - Mitigation: archive cold bundles and tighten retention.
- FM2: CI compute saturation due to heavy harness.
  - Mitigation: split suites into daily/weekly tiers.
- FM3: token spend spike from off-mission usage.
  - Mitigation: approval gate and tagging policy.

## Validation strategy
- Weekly budget variance report.
- Phase-end forecast recalibration.
- Simulated stress week to test headroom.

## Rollout/rollback
- Rollout budget controls from phase 1.
- If variance exceeds threshold, freeze non-critical work and rebalance.
- Rollback to last approved budget baseline when variance is unexplained.

## Risks and mitigations
- Risk: hidden spend from external tools.
  - Mitigation: lock external installs behind approval.
- Risk: underestimated reliability workload.
  - Mitigation: reserve dedicated reliability capacity upfront.

## Resource impact
Indicative monthly envelope (planning level):
- engineering effort: 40 dev equivalent
- CI/compute: medium-high
- storage: medium-high then stabilizing with compaction
- token/API: medium, controlled by workspace-only default

Evidence tags used: [P4][P7][R1][R2][R3][S1][S2].
