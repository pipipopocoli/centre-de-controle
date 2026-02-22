# 03_MEMORY_SYSTEM - Isolation, retention, compaction, promotion

## Context
Memory quality in Cockpit V2 is the core execution primitive. Variant D defines strict mechanics so retrieval is useful, reproducible, and safe.

## Problem statement
Raw memory growth without policy produces noise, retrieval instability, and contamination risk. A memory system must preserve signal while keeping reversible history.

## Proposed design
### Memory tiers
- Tier T0 Raw immutable
  - append-only logs, canonical truth for replay.
- Tier T1 Indexed chunks
  - chunked content linked to T0 row refs.
- Tier T2 Summaries
  - compaction outputs with provenance graph.
- Tier T3 Global Brain candidates
  - generic lessons pending @clems approval only.

### Chunking policy
- Chunk by semantic boundaries first, hard cap by token length [P2][P5].
- Store metadata: project_id, source_type, timestamp, owner_agent, sensitivity.
- Preserve deterministic chunk ids from content hash + metadata [ASSUMPTION-A4].

### Retention and expiry
- Hot window: 30 days full-index searchable.
- Warm window: 180 days summary-prioritized, raw on demand.
- Cold window: archive with manifest pointers and delayed restore.
- No auto-delete of audit-critical records without signed policy event.

### Compaction policy
- Trigger on size, staleness, and duplication ratio.
- Keep reversible links from summaries to raw references.
- Summaries tagged with confidence and evidence ids.

### Promotion rules to Global Brain
- Allowed only when all are true:
  1. Claim is generic and reusable.
  2. No project-specific identifiers remain.
  3. Evidence quality >= threshold.
  4. @clems explicit approval event exists.
- Promotion writes include rollback token and revocation path.

## Interfaces and contracts
- MemoryChunk
  - chunk_id
  - project_id
  - tier
  - source_ref
  - sensitivity
  - checksum
- CompactionDecision
  - run_id
  - trigger_reason
  - candidate_chunks[]
  - expected_gain
  - risk_flag
- PromotionDecision
  - decision_id
  - candidate_id
  - approved_by
  - status
  - revocation_token

## Failure modes
- FM-MEM-1: chunk hash collision.
- FM-MEM-2: summary hallucination detached from raw evidence.
- FM-MEM-3: mistaken promotion leaks project-specific detail.
- FM-MEM-4: retention policy removes needed forensic evidence.

## Validation strategy
- Collision tests on chunk id generation.
- Provenance integrity checks for summary nodes.
- Red-team contamination tests across synthetic projects.
- Retention drills with restore-time SLA checks.

## Rollout/rollback
- Rollout
  - Phase 1: Tier T0/T1 only.
  - Phase 2: controlled T2 compaction for one project.
  - Phase 3: T3 promotion queue with manual approval.
- Rollback
  - Disable higher tier feature flags.
  - Restore from previous manifest and replay deltas.

## Risks and mitigations
- Risk: over-aggressive compaction harms retrieval recall.
  - Mitigation: compaction gates with recall floor.
- Risk: tier complexity confuses operators.
  - Mitigation: operator-facing memory status panel with plain language states.

## Resource impact
- Storage reduction target from compaction: 25-45 percent [ASSUMPTION-A5].
- Added QA load: contamination harness and restore drills.

## Evidence tags used
[P2][P5][P6][P7][R1][R2][R5][S2][ASSUMPTION-A4][ASSUMPTION-A5]
