# 01_EXEC_SUMMARY - competitor-r1-d (Variant D memory engine)

## Context
Cockpit V2 needs a memory engine that is local-first, project-isolated, durable under failures, and still able to promote curated knowledge into Global Brain. Global Brain stays available for generic patterns, but retrieval for project logs/conversations/artifacts must remain project-scoped by default.

## Problem statement
Current planning risk is memory drift: mixed data roots, unclear promotion policy, and weak contamination barriers between projects. This can create wrong-context retrieval, operator confusion, and non-reproducible execution decisions.

## Proposed design
- Build a 4-layer memory stack:
  - Layer 0: raw append-only logs (chat, journal, events) [R1][S1].
  - Layer 1: FTS lexical index as baseline retrieval (BM25 style scoring) [P1][R2].
  - Layer 2: optional semantic index behind explicit gate and budget cap [P2][P3][R3].
  - Layer 3: Global Brain promotion queue, approved only by @clems and only for generic, de-identified learnings [ASSUMPTION-A1].
- Keep deterministic replay bundles with index snapshots and compaction manifests [P8][R1].
- Enforce strict policy checks before retrieval and promotion [S2][S3].

## Interfaces and contracts
- MemoryWriteRequest
  - project_id (required)
  - stream_type (chat|journal|artifact|event)
  - source_agent
  - payload
  - timestamp_rfc3339 [S2]
- MemorySearchRequest
  - project_id (required)
  - query
  - mode (fts|hybrid)
  - top_k
  - include_streams
- PromotionRequest
  - project_id
  - claim_id
  - evidence_ids
  - deidentification_proof
  - approver=@clems required
- Determinism contract
  - same dataset + same query + same config => stable top-k ordering within tolerance [ASSUMPTION-A2].

## Failure modes
- FM-1: Cross-project contamination through bad project_id routing.
- FM-2: Index corruption after crash during compaction.
- FM-3: Promotion of project-specific secrets into Global Brain.
- FM-4: Semantic index stale against lexical baseline.
- FM-5: Retrieval latency spikes under high write concurrency.

## Validation strategy
- Contract tests for read/write/isolation boundaries.
- Replay tests for deterministic retrieval on fixed corpus.
- Chaos tests for crash during compaction and recovery.
- Policy tests for promotion gate and @clems-only approval.
- Regression benchmark pack with precision@k, contamination rate, and p95 latency [P4][P5][P6].

## Rollout/rollback
- Rollout
  1. FTS-only baseline in shadow mode.
  2. Hybrid retrieval pilot for 1 project with budget caps.
  3. Promotion queue enabled with manual @clems review only.
  4. Wider rollout after gate pass.
- Rollback
  - Disable hybrid path flag.
  - Revert to last signed lexical snapshot.
  - Pause promotion queue and quarantine recent promotions.

## Risks and mitigations
- Risk: Overfit to semantic retrieval early.
  - Mitigation: FTS remains authoritative baseline until gate thresholds pass.
- Risk: Operator trust drop if results are unstable.
  - Mitigation: deterministic replay, signed snapshots, visible confidence tags.
- Risk: Policy bypass in automation.
  - Mitigation: server-side approval checks and immutable audit trail.

## Resource impact
- Team slice: 12 of 40 devs for memory subsystem across phases.
- Storage: +15-30 GB/project/year depending on retention profile [ASSUMPTION-A3].
- Compute: semantic indexing isolated with queue budget and throttles.
- Ops: daily compaction window plus weekly audit review.

## Evidence tags used
[P1][P2][P3][P4][P5][P6][P8][R1][R2][R3][S1][S2][S3][ASSUMPTION-A1][ASSUMPTION-A2][ASSUMPTION-A3]
