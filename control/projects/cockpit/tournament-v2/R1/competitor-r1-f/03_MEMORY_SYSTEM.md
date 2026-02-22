# Cockpit V2 R1 - Memory System

## Context
Cockpit V2 must preserve strict project isolation while still enabling useful long-term memory for agents and operators. Variant F adds a readability requirement: memory outputs must compress complexity into quick operator understanding without losing traceability.

## Problem statement
Current project memory can grow noisy and fragmented. Without a memory stack, operators either miss critical context or drown in raw logs. At the same time, cross-project contamination risk is unacceptable under locked constraints.

## Proposed design
### 1) Four-layer memory stack
1. Layer M0: raw append-only journals
- `chat/*.ndjson`, `agents/*/journal.ndjson`, run logs.
- Immutable source of truth for replay.

2. Layer M1: FTS baseline index (default)
- SQLite FTS5 per project.
- Fast lexical retrieval for incidents, decisions, and blockers.

3. Layer M2: compaction summaries
- Daily and weekly digests, plus open loops.
- Structured summary objects with backlinks to source events.

4. Layer M3: optional semantic index
- Project-scoped vector store, disabled by default.
- Activated only when FTS relevance fails threshold [ASSUMPTION-A5].

### 2) Promotion to Global Brain
Promotion is explicit and audited:
- Candidate item must be generic skill/protocol pattern.
- Must remove project-sensitive identifiers.
- Must include rationale and replay references.
- @clems approval required before publish.

No cross-project retrieval for chat/log/artifact content by default.

### 3) Compaction policy
- Daily compaction: summarize high-signal events.
- Weekly compaction: merge resolved loops, keep unresolved loops open.
- Retention: raw logs retained; compressed summaries versioned.
- Expiry: stale tactical summaries age out unless linked to decisions.

Design basis follows snapshot and auditability principles [P1][P2][P4].

## Interfaces and contracts
### Directory contracts
- Project raw: `control/projects/<project_id>/chat/`, `agents/`, `runs/`
- Memory index: `control/projects/<project_id>/memory/fts.db`
- Summaries: `control/projects/<project_id>/memory/summary/`
- Optional semantic: `control/projects/<project_id>/memory/semantic/`
- Promotion queue: `control/projects/<project_id>/memory/promotion_queue.ndjson`

### Query contract
Input:
```json
{
  "project_id": "cockpit",
  "query": "what changed in approvals this week",
  "mode": "fts_first",
  "max_items": 20
}
```

Output:
```json
{
  "items": [{"id": "evt_123", "score": 0.88, "source": "chat/global.ndjson"}],
  "summary": "Approval flow changed in ADR-007.",
  "trace": ["evt_102", "evt_111", "evt_123"]
}
```

### Promotion contract
`propose_promotion(item_id, sanitized_payload, rationale, evidence_refs)`
- Requires status `pending_approval` until @clems decision.

## Failure modes
- Index corruption: rebuild from raw append-only logs.
- Summary hallucination risk: enforce trace links for every summary sentence.
- Semantic contamination: keep embeddings project-scoped and encrypted at rest.
- Over-compaction: preserve link to original events and rollback summary version.
- Promotion leak: sanitize checks plus mandatory approval gate.

## Validation strategy
- Query relevance benchmark with curated incident questions.
- Deterministic rebuild tests from raw logs to FTS and summary stores.
- Contamination tests: ensure project A query never returns project B artifacts.
- Compaction regression tests: verify unresolved loops remain visible.
- Human validation: operators rate summary usefulness and correctness.

## Rollout/rollback
Rollout:
1. Enable M0 + M1 only.
2. Add M2 compaction with trace links.
3. Pilot M3 semantic layer on one project (opt-in).
4. Enable promotion queue with approval workflow.

Rollback:
- Disable M3 immediately if contamination or cost spikes.
- Rebuild M1/M2 from M0.
- Revert summary versions by timestamp.
- Freeze promotion queue pending policy review.

## Risks and mitigations
- Risk: summary drift from source truth. Mitigation: mandatory trace pointers and review gates.
- Risk: memory growth costs. Mitigation: compression and retention tiers [ASSUMPTION-A6].
- Risk: low retrieval quality with FTS only. Mitigation: optional semantic pilot behind feature flag.
- Risk: manual review bottleneck for promotions. Mitigation: batch review templates for @clems.

## Resource impact
- Baseline storage: low to moderate (text-heavy, compressed).
- CPU: modest, mostly indexing and summary generation.
- Engineering load: 1 data pod, 1 platform pod, 1 QA pod.
- Ops load: audit reviews for promotions and periodic compaction health checks.
