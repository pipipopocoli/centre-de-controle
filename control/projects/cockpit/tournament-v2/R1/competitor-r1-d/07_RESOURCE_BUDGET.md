# 07_RESOURCE_BUDGET - Operating envelope for Variant D

## Context
Memory architecture must fit realistic budget boundaries for API usage, storage, compute, and engineering time.

## Problem statement
Unbounded memory plans are not shippable. We need explicit operating envelopes with hard stop policies.

## Proposed design
### Budget categories
- Engineering capacity (40-dev program slice)
- Compute and indexing
- Storage and backups
- QA and regression infra
- Incident and operations overhead

### Envelope targets
- CPU budget
  - FTS indexing: predictable baseline on shared nodes.
  - Semantic indexing: queued and throttled by project budget.
- Storage budget
  - Raw + index + summary tiers with retention/archival policy.
- API/token budget
  - semantic operations bounded per project/day [ASSUMPTION-A9].

## Interfaces and contracts
- BudgetPolicy
  - project_id
  - daily_semantic_token_cap
  - indexing_cpu_quota
  - storage_quota
  - alert_thresholds
- BudgetEvent
  - timestamp
  - category
  - usage
  - threshold
  - action_taken

## Failure modes
- FM-BDG-1: semantic queue runaway creates spend spike.
- FM-BDG-2: storage overrun due to retention misconfiguration.
- FM-BDG-3: noisy alerts desensitize operators.

## Validation strategy
- Budget simulation per project profile (small/medium/large).
- Alert precision review: true positive ratio target > 0.8 [ASSUMPTION-A10].
- Monthly capacity review tied to actual growth curves.

## Rollout/rollback
- Rollout
  - start with conservative caps and burst tokens disabled.
  - tune after first month telemetry.
- Rollback
  - enforce hard caps and semantic queue pause if thresholds exceeded.

## Risks and mitigations
- Risk: under-budgeting harms retrieval quality.
  - Mitigation: controlled exceptions with expiry and postmortem.
- Risk: over-budgeting erodes sustainability.
  - Mitigation: cap-by-default, approval for increases.

## Resource impact
### Rough 4-month envelope (ASSUMPTION-A11)
- Engineering: 40 dev x 4 months.
- Infra compute: moderate baseline + optional burst windows.
- Storage: 5-15 TB aggregate depending on project count.
- QA: 2 dedicated runners for nightly full harness.

## Evidence tags used
[P2][P3][R1][R3][R7][S2][ASSUMPTION-A9][ASSUMPTION-A10][ASSUMPTION-A11]
