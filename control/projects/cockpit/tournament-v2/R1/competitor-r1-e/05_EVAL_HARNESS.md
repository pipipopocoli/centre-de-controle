# 05 - Eval Harness (Variant E core)

## Context
Cockpit V2 needs non-regression assurance before release. Variant E targets benchmark selection, replay packs, patch quality metrics, strict gates, and false-positive/false-negative controls.

## Problem statement
Without a formal eval harness, release decisions are noisy:
- regressions slip through,
- flaky checks block healthy patches,
- no deterministic evidence exists for incident replay,
- cost/time tradeoffs are not explicit.

## Proposed design
### 1) Benchmark portfolio
Use 4 complementary suites:
1. `B0-SMOKE` (5-10 min): sanity checks, schema checks, policy checks.
2. `B1-CONTRACT` (10-20 min): unit/integration contracts and deterministic replay core.
3. `B2-INCIDENT` (20-40 min): replay of curated production-like incidents.
4. `B3-STRESS` (nightly): scale/fault injection/cost envelope.

Scenario selection policy:
- each release candidate must run B0+B1,
- risk-tagged changes also run B2,
- B3 is nightly with release veto if critical regressions appear.

### 2) Replay pack contract
Directory contract:
- `manifest.json`
- `env.lock`
- `input/fixtures/`
- `input/seeds.json`
- `trace/events.ndjson`
- `output/patch.diff`
- `output/metrics.json`
- `output/verdict.json`

Manifest fields:
- `run_id`, `project_id`, `git_sha`, `scenario_profile`, `created_at`, `toolchain_hash`, `policy_version`.

Determinism rules:
- identical `toolchain_hash` + seed must reproduce equivalent gate verdict.
- if non-equivalent, run is marked `NON_DETERMINISTIC` and blocked pending triage.

### 3) Patch quality metrics
Core metrics (release relevant):
- `pass_rate`: test pass ratio.
- `critical_regressions`: count of new critical failures.
- `flake_delta_pp`: change in flaky failure percentage points.
- `median_runtime_min` and `p95_runtime_min`.
- `token_cost_usd` and `infra_cost_usd`.
- `policy_violation_count`.
- `replay_fidelity_score` (0-1).

Secondary metrics:
- `mttr_eval` (time to classify failure).
- `override_rate` by severity.
- `coverage_of_recent_incidents`.

### 4) Regression gates and thresholds
Hard fail (release blocking):
- `critical_regressions > 0`
- `pass_rate < 0.99` on B1
- `policy_violation_count > 0`
- `replay_fidelity_score < 0.95`

Soft fail (requires adjudication):
- `flake_delta_pp > 1.0`
- `p95_runtime_min > baseline * 1.25`
- `token_cost_usd > baseline * 1.20`

Pass:
- all hard-fail checks clear,
- at most one soft-fail and documented mitigation accepted.

### 5) False positive / false negative handling
FP controls:
- triage classifier tags failures as `BUG`, `FLAKE`, `INFRA`, `POLICY`.
- flaky scenarios move to quarantine lane with owner + expiry.
- retry budget (max 2) only for known flake signatures.

FN controls:
- weekly backfill from incident/postmortem corpus.
- mutation-style sentinel tests for critical workflows.
- shadow red-team scenarios on random sample of approved patches.

Adjudication policy:
- hard-fail override requires `@clems` with explicit rationale and expiry.
- repeated overrides for same scenario trigger mandatory benchmark redesign ticket.

### 6) Release packet
Every candidate release produces:
- gate verdict summary,
- confusion matrix snapshot,
- scenario coverage map,
- top risks + required follow-ups,
- rollback confidence statement.

## Interfaces and contracts
### Schema - `metrics.json`
```json
{
  "run_id": "string",
  "project_id": "string",
  "git_sha": "string",
  "suite": "B0|B1|B2|B3",
  "pass_rate": 0.0,
  "critical_regressions": 0,
  "flake_delta_pp": 0.0,
  "p95_runtime_min": 0.0,
  "token_cost_usd": 0.0,
  "infra_cost_usd": 0.0,
  "policy_violation_count": 0,
  "replay_fidelity_score": 0.0
}
```

### Schema - `verdict.json`
```json
{
  "run_id": "string",
  "gate_version": "string",
  "verdict": "PASS|SOFT_FAIL|HARD_FAIL|OVERRIDE_APPROVED",
  "blocking_reasons": ["string"],
  "override": {
    "approved": false,
    "actor": "@clems",
    "reason": "string",
    "expires_at": "ISO-8601"
  }
}
```

### NDJSON event contract
- one event per line,
- monotonic timestamp,
- mandatory keys: `ts`, `run_id`, `phase`, `event_type`, `payload_hash`.

## Failure modes
- Overfit benchmarks that miss real-world failure shape.
- Benchmark contamination from training artifacts.
- Toolchain hash mismatch creates fake nondeterminism.
- Gate engine outage blocks all merges.

## Validation strategy
- Historical replay campaign over 3 months of change history.
- Blind adjudication drill to measure FP/FN rates.
- Canary gate rollout on one workstream before global adoption.
- Monthly threshold recalibration with signed change log.

Success criteria (90-day):
- critical escaped defects down >= 40 percent,
- median eval triage time <= 30 min,
- hard-fail precision >= 0.90,
- hard-fail recall >= 0.95 on critical class.

## Rollout/rollback
Rollout phases:
1. Build and validate replay pack contract.
2. Shadow gates with no release blocking.
3. Soft block + mandatory triage notes.
4. Hard block for all release branches.

Rollback strategy:
- instant fallback to previous `gate_version`.
- disable newly introduced benchmark profiles.
- preserve artifacts and perform root-cause review within 24h.

## Risks and mitigations
- Risk: developer frustration from false blocks.
  - Mitigation: fast adjudication SLA + transparent scorecards.
- Risk: rising run time at 40-dev scale.
  - Mitigation: shard scheduler, suite stratification, nightly heavy runs.
- Risk: cost blow-up from token-heavy replays.
  - Mitigation: budget guardrails with automatic downgrade path.

## Resource impact
- Daily runs: ~350 to 700 eval jobs depending on commit cadence.
- Compute: 80 to 120 CPU-hours/day baseline, 2x burst support.
- Storage: 10 to 15 GB/day raw traces before compaction.
- Team staffing: 9 core FTE plus domain owners for scenario curation.

## References
Primary: [P1][P2][P3][P4][P5][P6][P7][P8]
Repos: [R1][R2][R3][R4][R5][R6]
Specs/docs: [S1][S2][S3]
