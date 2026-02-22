# 05_EVAL_HARNESS - Non Regression and Release Gates

## Context
- Variant C introduces scheduler and fallback complexity that must be validated before rollout.
- This harness defines deterministic replay packs and release-blocking thresholds.

## Problem statement
- Router and queue regressions can remain hidden until high-load incidents.
- We need repeatable tests that detect fairness collapse, retry storms, policy bypass, and replay drift.

## Proposed design
### 1) Benchmark suites
- Suite A: deterministic replay integrity.
- Suite B: queue fairness under mixed load.
- Suite C: provider outage and fallback correctness.
- Suite D: policy boundary enforcement.
- Suite E: cost and token envelope adherence.

### 2) Replay pack format
- `pack_id`
- `scenario_id`
- `seed`
- `event_trace`
- `expected_outcomes`
- `budget_limits`
- `version`

### 3) Gate thresholds
- G1 replay determinism >= 99 percent.
- G2 starvation incidents = 0 over 24h soak.
- G3 policy bypass incidents = 0.
- G4 p95 interactive queue wait under target.
- G5 budget overrun incidents = 0.

### 4) Regression policy
- Any fail in G1-G3 is release-blocking.
- G4-G5 allow one temporary waiver with @clems approval and fix ticket.

## Interfaces and contracts
### Harness run contract
- Input:
  - `suite_id`
  - `scenario_set`
  - `router_version`
  - `seed`
- Output:
  - `pass_fail`
  - `metric_bundle`
  - `regression_diff`
  - `evidence_refs`

### Metric contract
- `metric_id`
- `value`
- `threshold`
- `status`
- `trend`

## Failure modes
- FM-EVAL-01: flaky tests from non-deterministic fixtures.
- FM-EVAL-02: false pass due to weak expected outcomes.
- FM-EVAL-03: false fail due to unstable environment.
- FM-EVAL-04: incomplete replay pack coverage.

## Validation strategy
- Seeded runs with reproducibility checks.
- Golden replay packs for critical scenarios.
- Weekly false positive and false negative review.
- Coverage report by failure class.

## Rollout/rollback
- Rollout:
  - start with G1-G3 mandatory gates.
  - phase in performance and budget gates.
- Rollback:
  - freeze release lane and revert router version.
  - rerun baseline replay packs before unfreeze.

## Risks and mitigations
- Risk: gate fatigue slows delivery.
  - Mitigation: prioritize high-signal tests and retire low-signal cases.
- Risk: synthetic tests miss production edge cases.
  - Mitigation: add sampled production replay packs.

## Resource impact
- Team:
  - 6 devs eval harness core
  - 4 devs scenario authoring
  - 3 devs observability integration
- Infra:
  - replay pack storage
  - CI runners for soak and chaos tests

## Source pointers
- SRC-P5,SRC-P6,SRC-R1,SRC-R2,SRC-R7,SRC-D1.
