# 05_EVAL_HARNESS - Non-Regression And Release Gates For Skill Supply Chain

## Context
Cockpit V2 requires a non-regression harness that protects stability, security, and policy correctness while enabling continuous delivery. For Variant B, the harness focuses on skill lifecycle integrity, trust-tier controls, and cross-runtime parity.

References: P4, P8, P9, D1, D2, R2, R3, R5.

## Problem statement
Without a robust harness, regressions in verifier, policy, or runtime adapters can silently weaken security posture. Critical risks include:
- Policy bypass introduced by code or config changes.
- Replay non-determinism that breaks audit confidence.
- Revoke propagation regressions under load.
- Divergent outcomes across Codex and Antigravity runtimes.

We need deterministic, automated, release-blocking evaluation gates.

## Proposed design
### A. Test planes
1. Plane S - Supply chain integrity
- Manifest schema tests
- Signature verification tests
- Provenance validation tests
- SBOM and vulnerability policy tests

2. Plane L - Lifecycle correctness
- State-machine transition tests for install/update/revoke/quarantine
- Invalid transition denial tests
- Lockfile atomicity tests

3. Plane P - Policy and approvals
- Scope escalation denial tests
- Full-access requires `@clems` approval tests
- Trust-tier upgrade workflow tests

4. Plane R - Replay and determinism
- Same input + same lockfile => same decision trace
- Deterministic event ordering checks
- Run bundle integrity validation

5. Plane X - Cross-runtime parity
- Identical scenarios executed on Codex and Antigravity adapters
- Decision and lock resolution must match

6. Plane O - Operator clarity
- Incident response drills
- 60-second comprehension checks for dashboard and runbook

### B. Evaluation artifacts
- `scenario_pack.jsonl`
- `policy_bundle_snapshot.json`
- `expected_decisions.csv`
- `replay_bundle.tar.zst`
- `parity_report.md`
- `gate_result.json`

### C. Key metrics
- Integrity pass rate
- Policy false-positive and false-negative rates
- Revoke propagation latency (p50/p95/p99)
- Replay determinism score
- Cross-runtime parity score
- Mean time to contain compromised skill

## Interfaces and contracts
### Contract: `ScenarioCase`
Fields:
- `scenario_id`
- `category`
- `input_manifest_ref`
- `expected_policy_decision`
- `expected_state_transition`
- `runtime_provider`

### Contract: `GateThreshold`
Fields:
- `metric_name`
- `warning_threshold`
- `block_threshold`
- `evaluation_window`

### Contract: `GateResult`
Fields:
- `release_candidate_id`
- `status` (`pass`, `warn`, `block`)
- `failed_metrics[]`
- `failed_scenarios[]`
- `recommended_actions[]`

### Contract: `ReplayCheck`
Fields:
- `run_id`
- `bundle_hash`
- `decision_match` (bool)
- `event_order_match` (bool)
- `diff_summary`

### Release-blocking thresholds (initial)
- Signature/provenance verification pass < 100 percent => block.
- Policy false-negative > 0 percent on critical scenarios => block.
- Revoke propagation p95 > 10 min => block (A6 validation target).
- Cross-runtime parity < 99.9 percent => block.
- Replay determinism < 99.99 percent => block.

## Failure modes
- FM1: Flaky tests hide regressions.
  - Mitigation: quarantine flaky cases and enforce stability score on test suite.

- FM2: Synthetic scenarios miss real incidents.
  - Mitigation: include production replay packs and post-incident additions.

- FM3: Gate fatigue leads to threshold weakening.
  - Mitigation: change-control board for threshold updates.

- FM4: Large scenario packs slow CI too much.
  - Mitigation: tiered gates (fast, nightly, pre-release full).

- FM5: Parity harness itself drifts from runtime behavior.
  - Mitigation: harness version pin and independent verification jobs.

## Validation strategy
Validation plan for harness quality:
- Meta-tests: inject known defects and ensure harness blocks release.
- Backtesting: replay prior incidents and confirm detection.
- Mutation testing on policy rules.
- Time-to-detect measurements in staged chaos runs.
- Monthly external review of critical scenario coverage.

Target outcomes after stabilization:
- Critical regression escape rate near zero.
- Mean time to detect under 15 minutes for revoke and policy drift incidents.

## Rollout/rollback
Rollout:
1. Build baseline scenario packs from current incidents and known attack classes.
2. Run in non-blocking mode for two cycles.
3. Enable block mode for critical metrics.
4. Expand coverage with runtime parity and replay bundles.
5. Move thresholds to GA values after two stable releases.

Rollback:
- If false blocks spike, revert to previous threshold profile.
- Keep critical integrity checks always blocking.
- Temporarily disable non-critical planes while fixing harness regressions.

## Risks and mitigations
- Risk: Overfitting to known scenarios.
  - Mitigation: randomized adversarial scenario generation.

- Risk: High CI cost and runtime.
  - Mitigation: adaptive scheduling and caching.

- Risk: Governance conflict about blocking releases.
  - Mitigation: pre-agreed exception policy with incident sign-off.

- Risk: Lack of ownership for failed gates.
  - Mitigation: ticket auto-assignment by failed plane.

- Risk: Metrics manipulation.
  - Mitigation: immutable raw event logs and independent aggregation.

## Resource impact
- Engineering effort:
  - Dedicated QA/reliability team to maintain scenario packs.
  - Security engineering support for attack simulations.
- Infrastructure:
  - Compute and storage for replay packs and parity runs.
- Operational:
  - On-call integration to rapidly action blocking findings.
