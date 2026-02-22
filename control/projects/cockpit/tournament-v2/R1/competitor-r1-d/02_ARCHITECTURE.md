# 02_ARCHITECTURE - Memory Engine Architecture

## Context
Variant D prioritizes memory isolation, deterministic retrieval, and controlled promotion into Global Brain while preserving local-first behavior.

## Problem statement
Without explicit architecture boundaries, Cockpit risks mixed memory ownership, brittle retrieval quality, and unbounded operational cost.

## Proposed design
### Component map
- Ingest Gateway
  - Validates project_id, stream_type, schema version.
  - Writes append-only ndjson segments [R1][S1].
- Segment Store
  - Immutable chunks with manifest and checksum.
  - Segment rotation by size/time.
- FTS Indexer (baseline)
  - Tokenize + normalize + index chunk references [P1][R2].
- Semantic Indexer (optional)
  - Embedding queue, vector index, and version pin [P2][P3][P4][R3][R4].
- Retrieval Router
  - lexical_only or hybrid route based on policy and budget.
- Compaction Engine
  - summarize stale spans, archive raw pointers, preserve provenance.
- Promotion Engine
  - takes candidate insights, strips project-specific tokens, routes to @clems approval [ASSUMPTION-A1].
- Audit Ledger
  - immutable records: writes, reads, promotions, policy decisions.

### Data flow
1. Write request enters Ingest Gateway.
2. Validated payload goes to Segment Store.
3. FTS index update is synchronous baseline.
4. Semantic enqueue is async and policy-gated.
5. Retrieval hits router -> FTS or hybrid merge.
6. Compaction job creates summary nodes + provenance links.
7. Promotion candidates enter approval queue.

## Interfaces and contracts
- Segment manifest contract
  - segment_id
  - project_id
  - checksum
  - row_count
  - min_ts/max_ts
  - schema_version
- Retrieval response contract
  - result_id
  - source_stream
  - chunk_ref
  - score_lexical
  - score_semantic(optional)
  - confidence_tag
  - provenance
- Compaction manifest contract
  - compaction_run_id
  - input_segments[]
  - output_summary_ref
  - dropped_rows_count
  - reversible_ref

## Failure modes
- FM-ARCH-1: stale semantic index returns orphan chunk refs.
- FM-ARCH-2: compaction emits summary without provenance.
- FM-ARCH-3: checksum mismatch on manifest replay.
- FM-ARCH-4: retrieval router falls back silently without telemetry.

## Validation strategy
- Interface conformance tests on every contract.
- End-to-end replay run with checksum verification.
- Differential tests lexical vs hybrid to catch regressions.
- Audit completeness test: each read/write has ledger row.

## Rollout/rollback
- Rollout by feature flags:
  - memory_fts_enabled=true
  - memory_hybrid_enabled=false initially
  - memory_promotion_enabled=false initially
- Rollback policy:
  - If contract breach rate > threshold, revert to previous signed manifest and disable affected flag.

## Risks and mitigations
- Risk: architecture complexity creates delivery drag.
  - Mitigation: strict phaseing, FTS-first baseline, hybrid as optional module.
- Risk: promotion path introduces human bottleneck.
  - Mitigation: queue SLA + templated approval packets.

## Resource impact
- 5 squads:
  - ingest/store
  - indexing/retrieval
  - compaction/promotion
  - policy/audit
  - test/release gates
- infra baseline: SQLite + FTS5, optional vector backend per project.

## Evidence tags used
[P1][P2][P3][P4][R1][R2][R3][R4][S1][S2][ASSUMPTION-A1]
