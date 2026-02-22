# 03_MEMORY_SYSTEM - Isolation and Promotion Model

## Context
- Variant C centers on router orchestration, but memory contracts are part of runtime safety.
- Memory must remain project-isolated by default while Global Brain stays available for generic knowledge.

## Problem statement
- Router-level orchestration can accidentally cross memory boundaries if retrieval scope is ambiguous.
- We need strict memory access contracts aligned with policy gates and replay traceability.

## Proposed design
### 1) Memory stack
- Layer 1: Project Memory (default scope)
  - stores project conversations, logs, artifacts, run metadata.
  - retrieval allowed only within same `project_id`.
- Layer 2: Global Brain (generic scope)
  - stores generic skills, souls protocol notes, cross-project generic learnings.
  - no project-sensitive artifact ingestion without promotion gate.
- Layer 3: Optional Semantic Index (disabled by default)
  - used only if FTS recall is insufficient and approved by @clems.

### 2) Retrieval policy
- Default retrieval chain:
  - query project FTS index
  - if no match, query Global Brain generic index
  - never auto-query other project memory.
- Promotion policy to Global Brain:
  - candidate marked by owner
  - sensitivity check
  - evidence packet
  - @clems approval
  - promotion event logged

### 3) Compaction and retention
- FTS baseline for V2.
- Daily compaction job:
  - summarize stale run logs
  - preserve decision-critical records
  - attach provenance pointers
- Retention:
  - hot data: 30 days
  - warm summaries: 180 days
  - archived bundles: per compliance policy

## Interfaces and contracts
### Memory query contract
- Input:
  - `project_id`
  - `query_text`
  - `scope` (`project_only` or `global_generic`)
  - `requester_role`
- Output:
  - matched records
  - confidence
  - provenance IDs
- Error contract:
  - `SCOPE_DENIED`
  - `PROJECT_MISMATCH`
  - `INDEX_UNAVAILABLE`

### Promotion contract
- Input:
  - `candidate_id`
  - `source_project_id`
  - `sensitivity_label`
  - `evidence_refs`
  - `requested_by`
- Output:
  - `promotion_status`
  - `approval_ref`
  - `global_record_id`

## Failure modes
- FM-MEM-01: cross-project retrieval bug leaks private context.
- FM-MEM-02: over-aggressive compaction removes critical incident traces.
- FM-MEM-03: promotion without approval contaminates Global Brain.
- FM-MEM-04: semantic index false positives create wrong context injection.

## Validation strategy
- Cross-project contamination tests with sentinel documents.
- Compaction regression tests comparing pre/post key fact retention.
- Promotion audit test verifying approval refs for all promoted records.
- Query replay tests to ensure deterministic retrieval outputs.

## Rollout/rollback
- Rollout:
  - Phase 1: project FTS + strict scope deny rules.
  - Phase 2: promotion workflow with approvals and audit log.
  - Phase 3: optional semantic layer pilot (only with approval).
- Rollback:
  - disable semantic layer and revert to FTS-only.
  - block promotions if audit mismatch detected.

## Risks and mitigations
- Risk: hidden contamination path via shared tooling.
  - Mitigation: policy deny by default + integration tests.
- Risk: retrieval recall drop after compaction.
  - Mitigation: compaction quality score threshold.

## Resource impact
- Memory infra:
  - FTS indexes per project.
  - compacted summary store.
  - promotion audit log.
- Team:
  - 5 devs memory engine
  - 3 devs policy/audit integration

## Source pointers
- SRC-D1,SRC-P1,SRC-P5,SRC-R7.
- Assumptions: ASSUMPTION-A1, ASSUMPTION-A5, ASSUMPTION-A8.
