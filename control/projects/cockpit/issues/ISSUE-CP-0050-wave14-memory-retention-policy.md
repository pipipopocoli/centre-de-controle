# ISSUE-CP-0050 - Wave14 Memory Retention Policy

- Owner: nova
- Phase: Plan
- Status: Open

## Objective
Implement project memory retention policy (7d/30d/90d/permanent archive) with strict isolation.

## Scope (In)
- `app/services/memory_index.py`
- `app/data/store.py`
- `control/projects/*/agents/*/memory.md`
- `control/projects/*/chat/*.ndjson`
- `scripts/` memory maintenance tooling

## Done (Definition)
- [ ] Retention tiers configurable and enforced per project.
- [ ] Compression/archive path for permanent memory documented and testable.
- [ ] No cross-project retrieval introduced.
- [ ] Operator report shows retention status and next compaction action.

## Constraints
- preserve audit trail
- no destructive delete without explicit policy path
