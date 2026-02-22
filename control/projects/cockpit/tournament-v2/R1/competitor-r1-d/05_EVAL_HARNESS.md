# 05_EVAL_HARNESS - Non-regression and release gates for memory engine

## Context
Variant D must prove memory quality does not regress under load, compaction, or policy changes.

## Problem statement
Without a dedicated harness, memory changes can silently degrade retrieval quality, violate isolation, or destabilize latency.

## Proposed design
### Harness pillars
- H1 Isolation tests
  - cross-project contamination rate target = 0.
- H2 Retrieval quality tests
  - precision@k, recall@k on gold datasets [P4][P6][P7].
- H3 Deterministic replay tests
  - same input pack reproduces ranked outputs.
- H4 Reliability tests
  - crash-recovery, corruption detection, manifest integrity.
- H5 Policy tests
  - promotion and scope approvals enforce role constraints.

### Gate thresholds
- Gate G1 contamination: 0 leakage events in test corpus.
- Gate G2 lexical baseline: p95 latency <= 250ms on standard set [ASSUMPTION-A6].
- Gate G3 hybrid mode: quality gain >= 8 percent over lexical baseline [ASSUMPTION-A7].
- Gate G4 replay determinism: >= 99.5 percent stable rank positions [ASSUMPTION-A2].
- Gate G5 policy: 100 percent approval trace coverage for elevated actions.

## Interfaces and contracts
- EvalPack
  - pack_id
  - project_fixture
  - query_set
  - expected_rank_refs
  - policy_cases
- EvalResult
  - pack_id
  - metric_values
  - threshold_pass
  - evidence_ref
- ReleaseDecision
  - release_id
  - gate_summary
  - blocker_list
  - rollback_plan

## Failure modes
- FM-EVAL-1: false positives block safe releases.
- FM-EVAL-2: false negatives allow contamination bug.
- FM-EVAL-3: metrics drift due to fixture changes.

## Validation strategy
- Frozen fixtures with checksum and version pin.
- Shadow runs before release gate enforcement.
- Weekly calibration on failed/near-fail cases.

## Rollout/rollback
- Rollout
  - advisory mode for 2 sprints.
  - blocking mode after calibration.
- Rollback
  - fallback to previous gate profile if noise spikes.

## Risks and mitigations
- Risk: benchmark gaming.
  - Mitigation: hidden holdout set and rotating query packs.
- Risk: expensive eval runs.
  - Mitigation: tiered run strategy (smoke, full, nightly).

## Resource impact
- Dedicated QA harness squad (6 dev + 2 QA).
- CI runtime increase 15-30 percent depending on full gate frequency.

## Evidence tags used
[P4][P6][P7][R7][S1][ASSUMPTION-A2][ASSUMPTION-A6][ASSUMPTION-A7]
