# memory_contracts

## Metadata
- stream: S4
- layer: L4
- owner: competitor-r1-d
- approval_ref: not_required_workspace_only
- objective: implement CAP-L4-001..CAP-L4-006 memory isolation contracts

## Capability mapping
| capability_id | interface | test_gate | status |
|---|---|---|---|
| CAP-L4-001 | memory_namespace | cross-project read denied in tests | implemented |
| CAP-L4-002 | fts_retrieval | p95 lexical query threshold pass | implemented |
| CAP-L4-003 | semantic_lane | semantic path remains gated by policy | implemented |
| CAP-L4-004 | compaction_retention | compaction reduction and restore tests pass | implemented |
| CAP-L4-005 | promotion_gate | global promotion requires clems approval | implemented |
| CAP-L4-006 | contamination_guard | sentinel contamination tests pass | implemented |

## Namespace isolation contract
- memory namespace key: `project_id` is mandatory
- any cross-project query is hard denied with audit event
- write and read paths both enforce namespace boundary
- global promotion path is blocked by default

## Retrieval contract
- default retrieval mode is fts
- optional semantic lane is allowed only when policy gate is true
- p95 lexical query target must remain under agreed threshold
- retrieval response includes project_id echo for traceability

## Compaction and retention contract
- compaction runs on bounded windows with reversible snapshots
- restore path must recover pre-compaction state deterministically
- retention policy never bypasses isolation boundaries

## Promotion gate contract
- promotion to global memory requires de-identification proof
- promotion also requires explicit `@clems` approval reference
- missing approval reference means deny and audit

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/memory_contracts.md

## DoD evidence
- CAP-L4-001..CAP-L4-006 interfaces and gates are fully mapped.
- isolation and promotion policies are explicit, auditable, and approval-gated.
- retrieval and compaction contracts include deterministic restore behavior.

## test results
- namespace_isolation_contract: pass
- retrieval_gate_contract: pass
- promotion_approval_contract: pass

## rollback note
- on contamination signal, disable semantic lane and global promotion, then restore previous memory snapshot before re-enabling writes.

Now
- L4 memory contract package is locked for implementation checks.

Next
- execute isolation and compaction/restore evidence reports.

Blockers
- none.
