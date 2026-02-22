# 03_MEMORY_SYSTEM - Isolated Memory With Supply-Chain Telemetry

## Context
Cockpit V2 requires project memory isolation by default, while Global Brain remains available for generic skills, souls, protocols, and reusable learnings. Variant B adds a memory requirement: all skill lifecycle decisions must be auditable, replayable, and resistant to cross-project contamination.

Relevant references: P8, P9, D1, D2, R8.

## Problem statement
Skill supply chain governance fails when memory systems do not cleanly separate:
- Project-specific evidence (who installed what, where, and why).
- Global reusable knowledge (approved patterns, known bad digests, protocol guidance).
- Ephemeral runtime traces (worker-level data).

If these boundaries blur, Cockpit risks policy violations, compliance issues, and incident confusion.

## Proposed design
### A. Memory tiers
1. Tier M0 - Ephemeral run memory
- Scope: single run, worker-lifetime only.
- Content: transient execution context.
- Retention: deleted at run end except hashed replay artifacts.

2. Tier M1 - Project operational memory (isolated)
- Scope: one project only.
- Content: skill lock history, approvals, decision traces, run bundles, incident notes.
- Retrieval: project-bound only.

3. Tier M2 - Project curated memory (isolated)
- Scope: one project only.
- Content: distilled project lessons and recommended policies.
- Promotion: manual and auditable.

4. Tier M3 - Global Brain generic memory
- Scope: all projects.
- Content: generic policies, templates, safe skill patterns, banned signatures.
- No raw project logs/conversations by default.

### B. Retrieval stack
- Baseline: FTS index per project (`fts_project_{project_id}`).
- Optional semantic layer: embedding index per project (not cross-project by default).
- Query broker enforces `project_id` filter before any retrieval.
- Global Brain queries are separate and only return generic entries tagged `global_generic=true`.

ASSUMPTION (A9): Existing stores can absorb FTS indexing without major downtime.

### C. Compaction and summarization
- Daily compaction: collapse repetitive run logs into summary chunks.
- Weekly promotion candidates: top stable patterns, repeated incidents, solved runbooks.
- Promotion gate: only `@clems` can approve M2 -> M3 promotion.
- Every promoted record must include redaction proof and contamination check.

### D. Promotion rules to Global Brain
A record is promotable only if:
- It is generic and reusable.
- It contains no project identifiers, logs, or secrets.
- It has at least one evidence link and one owner.
- It passed contamination classifier and manual review.

### E. Memory object model
- `MemoryRecord`: `record_id`, `scope`, `project_id`, `type`, `payload_ref`, `created_by`, `created_at`.
- `PromotionRequest`: `source_record_id`, `proposed_generic_text`, `risk_tags`, `review_status`.
- `RetentionPolicy`: `scope`, `hot_days`, `cold_days`, `delete_mode`.
- `ReplayPointer`: `run_id`, `bundle_hash`, `storage_uri`, `integrity_status`.

## Interfaces and contracts
### Contract: `MemoryWritePolicy`
- Enforces allowed scope per caller role.
- Denies cross-project writes and reads except explicit global generic APIs.

### Contract: `MemoryQuery`
Required fields:
- `scope` (`project`, `global`)
- `project_id` (required for project scope)
- `query_text`
- `max_results`
- `include_replay_refs` (bool)

### Contract: `PromotionDecision`
Required fields:
- `request_id`
- `decision`
- `reviewer` (must support `@clems` for final approve)
- `contamination_check_report`
- `timestamp`

### Contract: `CompactionJob`
Required fields:
- `project_id`
- `window_start`, `window_end`
- `input_record_count`
- `output_record_count`
- `summary_hash`

## Failure modes
- FM1: Cross-project filter bug leaks memory.
  - Mitigation: defense in depth with API filter + storage namespace + query sanitizer.

- FM2: Over-aggressive compaction drops forensic value.
  - Mitigation: preserve immutable replay pointers and original hashes.

- FM3: Promotion contamination slips through.
  - Mitigation: mandatory dual review and automated PII/entity scan.

- FM4: FTS index lag causes stale retrieval.
  - Mitigation: freshness SLO and index catch-up workers.

- FM5: Replay artifacts expire too early.
  - Mitigation: retention policy with legal/compliance minimums and storage alarms.

## Validation strategy
- Unit tests for scope enforcement and query filtering.
- Integration tests for promotion workflow and contamination gates.
- Red-team tests for cross-project query attempts.
- Replay validation: random sample re-execution must match decision traces.
- Freshness tests for FTS and optional semantic index.

Metrics:
- Cross-scope leak incidents: target zero.
- Retrieval freshness p95 under 60 seconds for new records.
- Promotion rejection rate due to contamination above baseline during initial hardening.

## Rollout/rollback
Rollout:
1. Add project namespace and strict query contracts.
2. Enable FTS per project.
3. Introduce compaction jobs in observe mode.
4. Enable promotion workflow with `@clems` approval.
5. Add semantic layer optionally for selected projects.

Rollback:
- Disable semantic layer first while keeping FTS baseline.
- Suspend promotion workflow if contamination risk rises.
- Revert to previous retention config if data loss risk is detected.

## Risks and mitigations
- Risk: Storage cost growth from replay retention.
  - Mitigation: hot/cold tiering and retention tuning (A5).

- Risk: Manual review fatigue for promotions.
  - Mitigation: better candidate ranking and auto-reject heuristics.

- Risk: Insufficient retrieval precision in FTS-only mode.
  - Mitigation: optional semantic index behind project flag.

- Risk: Legal constraints on retention by region.
  - Mitigation: region-aware retention policy templates.

- Risk: Ambiguity in generic vs project-specific content.
  - Mitigation: strict content taxonomy and linter for promotable records.

## Resource impact
- Data services:
  - Additional per-project indexes.
  - Compaction workers.
  - Promotion workflow tables.
- Compute:
  - Moderate steady load from compaction/index updates.
  - Optional semantic layer increases vector compute/storage.
- Human ops:
  - Memory curator role for weekly promotion review.
  - Security/compliance reviewer for contamination audits.
