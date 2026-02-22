# 03 - Memory System (Isolation + Eval observability)

## Context
Cockpit V2 already mandates project memory isolation and a Global Brain for generic learnings. Eval harness quality depends on precise replay context, not broad cross-project retrieval.

## Problem statement
Evaluation systems fail when memory contains mixed provenance, missing context, or stale summaries. We need memory rules that preserve isolation while still allowing reusable generic learnings.

## Proposed design
### Memory layers
1. Project Operational Memory (strictly isolated):
- run artifacts, eval metrics, decisions, incident traces.
2. Project Summaries (curated):
- weekly compaction from raw logs to durable summaries.
3. Global Brain (generic only):
- abstract patterns, reusable protocols, no project-private payload.

### Retrieval strategy
- Baseline retrieval: FTS over project-local index.
- Optional semantic layer: project-local embeddings only.
- Promotion policy to Global Brain:
  - allowed only for generalized, de-identified learnings,
  - requires `@clems` approval + provenance link.

### Compaction model
- `hot` 0-14 days: full fidelity logs.
- `warm` 15-90 days: compacted summaries + selected traces.
- `cold` >90 days: compressed archive with retrieval manifest.

## Interfaces and contracts
- Memory write contract:
  - every write includes `project_id`, `source_type`, `retention_tier`, `provenance_id`.
- Promotion contract:
  - `POST /memory/promotions` with `{artifact_id, abstraction_note, approval_actor}`.
- Contamination guardrail:
  - query planner rejects cross-project reads unless explicit approved exception exists.

## Failure modes
- Contamination by accidental cross-project indexing.
- Semantic layer drift from embedding model upgrade.
- Over-compaction deletes replay-critical context.
- Promotion errors leak sensitive project detail.

## Validation strategy
- Isolation tests: cross-project retrieval attempts must fail by default.
- Golden replay tests: old incidents must remain reproducible after compaction.
- Promotion audit: weekly review of all Global Brain promotions.
- Embedding drift monitor: compare retrieval quality pre/post model update.

## Rollout/rollback
- Rollout:
  - enable FTS first,
  - enable semantic layer behind feature flag,
  - enable promotion workflow after audit pass.
- Rollback:
  - disable semantic retrieval,
  - revert to previous index snapshot,
  - pause promotions pending review.

## Risks and mitigations
- Risk: memory growth costs.
  - Mitigation: retention tiers + dedupe + compression.
- Risk: poor retrieval relevance.
  - Mitigation: blended ranking (FTS + semantic), periodic relevance checks.
- Risk: policy bypass.
  - Mitigation: signed approvals and immutable promotion logs.

## Resource impact
- Index infra: moderate CPU for FTS rebuild windows.
- Storage: predictable tiered growth, target <= 500 GB/project/year in baseline.
- Human ops: 1 rotating memory steward per week.

## References
Key sources: [P3][P4][R2][R7][S1], plus assumptions [A2][A4].
