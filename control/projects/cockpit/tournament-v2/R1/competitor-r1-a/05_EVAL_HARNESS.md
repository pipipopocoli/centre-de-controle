# 05_EVAL_HARNESS

## Context
Variant A requires proof that persistence and replay are stable under failures. A non-regression harness is mandatory before broad rollout.

## Problem statement
Without a reproducible eval harness, defects in persistence only appear in production and are expensive to debug.

## Proposed design
### Harness goals
- Prove deterministic replay at run-bundle level.
- Detect corruption early.
- Validate retry/timeouts/backoff state machine behavior.
- Block release on regression thresholds.

### Test suites
- Suite A: Deterministic replay pack.
- Suite B: Crash injection pack.
- Suite C: Corruption and checksum pack.
- Suite D: Policy/approval conformance pack.
- Suite E: Performance envelope and saturation pack.

### Core metrics
- replay_hash_match_rate
- rollback_success_rate
- corruption_detection_latency
- duplicate_event_rate
- approval_bypass_incidents
- p95_recovery_time

Threshold policy (release blocking):
- replay_hash_match_rate < 99.9% blocks
- any approval_bypass_incident blocks
- duplicate_event_rate above threshold blocks
- corruption_detection_latency above SLO blocks

## Interfaces and contracts
Harness run contract:
- `harness_run_id`
- `suite_id`
- `scenario_id`
- `input_bundle_id`
- `expected_digest`
- `actual_digest`
- `pass_fail`
- `timestamp`

Regression pack contract:
- immutable scenario definitions
- versioned fixture bundle set
- deterministic seed policy

## Failure modes
- FM1: flaky tests caused by non-deterministic environment.
  - Mitigation: fixed seeds and controlled runtime profiles.
- FM2: false positives from strict thresholds.
  - Mitigation: calibration windows and trend-based override with audit.
- FM3: false negatives from narrow scenario coverage.
  - Mitigation: scenario expansion and adversarial fuzzing lane.

## Validation strategy
- Daily replay suite on latest build.
- Per-PR smoke for critical persistence components.
- Weekly chaos run with crash and corruption matrix.
- Monthly rollback drill with on-call simulation.

## Rollout/rollback
- Rollout:
  - start as advisory dashboards
  - move to soft gates
  - then hard release gates
- Rollback:
  - if harness instability detected, fall back to previous stable fixture version
  - keep hard gates for policy bypass regardless of harness version

## Risks and mitigations
- Risk: harness runtime cost grows with scenario count.
  - Mitigation: tiered schedule and selective gating by risk class.
- Risk: noisy alert fatigue.
  - Mitigation: severity model and route-based alert suppression.
- Risk: brittle fixture maintenance.
  - Mitigation: fixture generation tooling and ownership rotation.

## Resource impact
- CI compute: medium-high for crash and replay suites.
- Storage: medium for fixture bundles and results history.
- Team: dedicated reliability QA lane.

Evidence tags used: [P7][P8][R1][R2][R3][R6][S1][S2].
