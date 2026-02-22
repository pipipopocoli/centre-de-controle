# Cockpit V2 R1 - Eval Harness and Regression Gates

## Context
Cockpit V2 requires a non-regression harness that validates reliability, policy safety, and operator clarity. Variant F adds a hard acceptance criterion: 60-second comprehension during pressure scenarios.

## Problem statement
Without repeatable evaluation packs and quantitative gates, improvements in one area can silently break another (for example, prettier UX but slower updates, or better summaries but less deterministic replay).

## Proposed design
### 1) Harness architecture
- `scenario_packs/`: curated project snapshots and event timelines.
- `replay_runner/`: replays update pipeline against frozen inputs.
- `metric_collector/`: computes latency, determinism, comprehension, policy violations.
- `gate_engine/`: blocks release if thresholds fail.
- `report_exporter/`: writes markdown + json reports.

### 2) Scenario taxonomy
1. Normal flow: low blocker count, regular progress.
2. Degraded flow: stale signals, partial data gaps.
3. Incident flow: multiple blockers, failing tests, approval backlog.
4. Adversarial flow: malformed inputs, queue spikes, policy edge cases.

### 3) Core metrics and thresholds
Reliability:
- Replay determinism pass rate >=99.9 percent.
- p95 update latency <=6 seconds.
- p99 update latency <=12 seconds.

Clarity:
- 60-second comprehension success >=85 percent (release floor), >=90 percent target.
- Wrong-action recommendation rate <=5 percent.
- Signal misread rate on top charts <=8 percent [P9].

Safety:
- Unapproved full-access attempts = 0.
- Cross-project retrieval violations = 0.

Resilience:
- Last-good HTML recovery success = 100 percent on renderer failure tests.

## Interfaces and contracts
### Scenario pack contract
`scenario_packs/<pack_id>/`
- `inputs/` (state, roadmap, decisions, logs)
- `expected/summary.json`
- `expected/policy_flags.json`
- `notes.md`

### Replay result contract
`results/<run_id>.json`
```json
{
  "pack_id": "incident_007",
  "determinism": {"pass": true, "hash_match": true},
  "latency_ms": {"p50": 2100, "p95": 5400, "p99": 9800},
  "clarity": {"comprehension_pass_rate": 0.88, "misread_rate": 0.06},
  "safety": {"approval_violations": 0, "isolation_violations": 0},
  "verdict": "pass"
}
```

### 60-second comprehension test contract
Prompted operator questions (example):
1. Current phase?
2. Top blocker owner?
3. Next milestone date?
4. Any blocked high-risk action?
5. Is data stale warning active?

Pass requires >=4/5 correct in <=60s.

## Failure modes
- False positives from unstable thresholds: gate tuning with rolling baseline.
- False negatives from narrow scenario packs: expand adversarial packs monthly.
- Human test inconsistency: standardized script and timer tooling.
- Metric drift due environment variance: baseline hardware profile and normalization.

## Validation strategy
- Daily smoke packs on latest branch.
- Weekly full replay sweep across all packs.
- Monthly red-team scenario injection.
- Quarterly recalibration of comprehension thresholds with UX research.
- Compare against production incidents for external validity [ASSUMPTION-A2].

## Rollout/rollback
Rollout:
1. Shadow reporting only (no gate).
2. Soft gate with warnings.
3. Hard release gate for determinism, safety, and comprehension.

Rollback:
- Disable hard gate only with explicit @clems override.
- Keep safety gate active even during rollback.
- Freeze deployments until failing dimension has mitigation PR.

## Risks and mitigations
- Risk: team gaming metrics. Mitigation: rotating hidden scenario packs.
- Risk: overfitting to harness. Mitigation: inject random incident narratives.
- Risk: expensive human test loops. Mitigation: split into daily automated + weekly human sessions.
- Risk: threshold churn causes confusion. Mitigation: threshold change ADR and changelog entry.

## Resource impact
- Requires dedicated QA pod and tooling support.
- Human test budget: 2-4 hours/week from operator panel.
- Compute overhead: low to moderate, mostly replay and rendering.
- Large payoff: catches regressions before operator trust is lost.
