# 03_MEMORY_SYSTEM

## Context
Cockpit V2 memory must preserve strict project isolation while still allowing a curated Global Brain for generic knowledge. Variant A emphasizes persistence integrity and replay-safe memory operations.

## Problem statement
Without a clear memory stack, teams either over-share data across projects or lose important context after crashes. Both outcomes break reliability and governance.

## Proposed design
### Memory stack layers
- Layer 1: Project KV and append-only journal.
- Layer 2: Project FTS index (baseline retrieval).
- Layer 3: Optional semantic index, disabled by default.
- Layer 4: Compaction summaries for long history.
- Layer 5: Promotion queue for Global Brain candidates.

### Isolation model
- Hard namespace boundary per project_id.
- No cross-project retrieval by default.
- Promotion into Global Brain only for generic, de-identified, approved artifacts.

### Persistence model
- Write path: journal append -> checksum verify -> index update.
- Read path: checkpoint + journal tail rebuild when needed.
- Replay path: memory mutations rebuilt from deterministic event log.

### Compaction and retention
- Hot window: full fidelity.
- Warm window: summarized clusters with source pointers.
- Cold window: archived snapshots, still replayable.
- Promotion candidates survive compaction only with approval metadata.

## Interfaces and contracts
Memory item contract:
- `item_id`
- `project_id`
- `source_type`
- `content_digest`
- `created_at`
- `updated_at`
- `retention_tier`
- `promotion_state`
- `approval_id` (nullable)

Promotion contract:
- `candidate_id`
- `project_id`
- `genericity_score`
- `sensitivity_score`
- `approval_required`
- `approval_id`
- `promoted_at`

Index contract:
- FTS index is canonical baseline.
- semantic index is optional and never bypasses FTS access controls.

## Failure modes
- FM1: index drift from journal tail.
  - Mitigation: periodic replay check and index rebuild job.
- FM2: accidental cross-project query.
  - Mitigation: policy guard at query planner with hard project_id filter.
- FM3: compaction drops required legal/audit evidence.
  - Mitigation: retention policy with non-deletable audit classes.
- FM4: promotion of sensitive project content.
  - Mitigation: sensitivity classifier + mandatory approval.

## Validation strategy
- Differential test between FTS-only and FTS+semantic modes.
- Replay test to rebuild memory from scratch and compare digests.
- Isolation fuzz tests with adversarial project IDs.
- Promotion tests to ensure approval-required paths fail closed.

## Rollout/rollback
- Rollout starts with FTS-only.
- Add semantic layer per project behind feature flag.
- Enable compaction once replay validation reaches target pass rate.

Rollback:
- Disable semantic layer first.
- Restore from last checkpoint and replay journal.
- Freeze promotions if classifier drift detected.

## Risks and mitigations
- Risk: semantic retrieval contamination.
  - Mitigation: keep semantic optional and policy-gated.
- Risk: storage pressure from append-only logs.
  - Mitigation: retention tiers plus snapshot cadence.
- Risk: promotion bottleneck.
  - Mitigation: asynchronous review queue with SLA targets.

## Resource impact
- Storage: moderate increase due to immutable journal retention.
- CPU: medium for compaction and replay checks.
- Team: dedicated memory lane with policy reviewer support.

Evidence tags used: [P3][P5][P7][R2][R4][R6][S1][S2].
