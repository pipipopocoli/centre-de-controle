# ISSUE-CP-0050 - Wave14 Memory Retention Policy

- Owner: nova
- Phase: Ship
- Status: Done

## Objective
Implement project memory retention policy (7d/30d/90d/permanent archive) with strict isolation.

## Scope (In)
- `app/services/memory_index.py`
- `app/data/store.py`
- `control/projects/*/agents/*/memory.md`
- `control/projects/*/chat/*.ndjson`
- `scripts/` memory maintenance tooling

## Done (Definition)
- [x] Retention tiers configurable and enforced per project.
- [x] Compression/archive path for permanent memory documented and testable.
- [x] No cross-project retrieval introduced.
- [x] Operator report shows retention status and next compaction action.

## Constraints
- preserve audit trail
- no destructive delete without explicit policy path

## Closeout
- Closed at: 2026-02-23T10:40Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_CP0050_MEMORY_RETENTION_2026-02-23.md`
- Runtime artifact:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json`
