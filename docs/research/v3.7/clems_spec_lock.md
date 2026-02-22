# V3.7 Spec Lock (Clems)

Date: 2026-02-13
Project lock: cockpit

## Goal
- Deliver Leo Phase 1 stable without scope creep.
- Keep automation stable while introducing deterministic memory search and strict team hierarchy.

## Runtime baseline (cockpit)
- Source: ~/Library/Application Support/Cockpit/projects/cockpit/runs/auto_mode_state.json
- schema_version: 3
- processed_ids: 325
- request_entries: 32
- last_stats:
  - dispatched: 0
  - skipped: 375
  - skipped_duplicate: 375
  - skipped_wrong_project: 0
  - skipped_internal_agent: 0
- kpi snapshot (external_only=true):
  - open_external_total: 0
  - close_rate_24h: 0.00
  - reminder_noise_pct: 0.00

## Locked decisions
- Memory canonical source remains memory.md per agent.
- memory.proposed.md remains non-destructive output.
- Add local SQLite FTS5 search by project only (no cross-project retrieval).
- Team hierarchy is strict:
  - L0: clems
  - L1: victor, leo
  - L2: agent-N
- No vector store in this phase.

## Non-goals
- No platform abstraction rewrite.
- No token/cost tracking dashboard.
- No cross-project memory retrieval.

## Acceptance focus
- Agent cards grouped by L0/L1/L2 and mission visibility improved.
- Deterministic memory index build/search and compaction.
- Zero cross-project leak in memory search path.
