# V3.7 Backend Spec (Victor)

Date: 2026-02-13
Project lock: cockpit

## Scope
- Add deterministic memory index (SQLite FTS5, per project).
- Add strict agent registry with L0/L1/L2 metadata.
- Extend memory compaction script to support runtime projects root.

## Memory index design
- Service: app/services/memory_index.py
- Input documents:
  - STATE.md
  - ROADMAP.md
  - DECISIONS.md
  - agents/*/memory.md
  - agents/*/memory.proposed.md
  - agents/*/journal.ndjson tail
  - chat/global.ndjson tail
- Output DB:
  - runs/memory_index.sqlite3
  - table memory_fts (fts5)
  - table memory_meta (project_id, built_at, docs_indexed)
- Determinism:
  - stable source ordering by path
  - stable search ordering by score then path

## Agent registry design
- Path: agents/registry.json
- Entry schema:
  - agent_id
  - name
  - engine
  - level (0..2)
  - lead_id (null for level 0)
  - role
- Fallback defaults:
  - clems -> level 0
  - victor, leo -> level 1, lead clems
  - agent-N -> level 2, lead victor (odd) or leo (even)

## Complexity + risks
- FTS5 availability depends on local sqlite build.
  - Mitigation: tests fail fast with clear error.
- Registry drift if state.json and registry diverge.
  - Mitigation: save_project normalizes and writes registry every save.

## QA commands
- ./.venv/bin/python scripts/memory_index.py --project cockpit --query "run loop"
- ./.venv/bin/python tests/verify_memory_compaction.py
- ./.venv/bin/python tests/verify_memory_index.py
- ./.venv/bin/python tests/verify_agent_registry.py
- ./.venv/bin/python tests/verify_auto_mode.py

## Success criteria
- Deterministic search hits for same query.
- No cross-project memory results.
- Registry defaults and overrides persist across reload.
