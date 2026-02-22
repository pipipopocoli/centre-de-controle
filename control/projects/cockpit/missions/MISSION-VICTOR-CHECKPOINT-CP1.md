# Mission - Clems to Victor - CP-01 Backend Push

Objective
- Deliver backend lane of checkpoint CP-01 through delegated specialist execution.

Scope (In)
- ISSUE-CP-0001 skills catalog fetch/cache/fallback.
- ISSUE-CP-0002 policy engine curated fail-open.
- ISSUE-CP-0003 installer wrapper idempotence.
- ISSUE-CP-0004 memory index generator.
- ISSUE-CP-0005 MCP skills tools.

Scope (Out)
- UI layout and interaction polish.
- Non-checkpoint features.

Files allowed
- /Users/oliviercloutier/Desktop/Cockpit/app/**
- /Users/oliviercloutier/Desktop/Cockpit/control/**
- /Users/oliviercloutier/Desktop/Cockpit/scripts/**
- /Users/oliviercloutier/Desktop/Cockpit/tests/**
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/**

Done
- Each issue has verifiable output (diff + test/log proof).
- Each issue has a single owner and status update in chat.
- Wave 1 must close before Wave 2 starts.

Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_basic.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_auto_mode.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_index.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_compaction.py`

Risks
- Contract drift between MCP tools and existing clients.
- Non-deterministic memory ordering.

First 2 subtasks (optional)
- Dispatch Wave 1 to @agent-1, @agent-2, @agent-3.
- Keep @agent-4, @agent-5 queued until Wave 1 merge + smoke.

## Delegation Subtasks

### Subtask for @agent-1
Objective
- Implement ISSUE-CP-0001.

Constraints
- Do not change UI files.
- Keep behavior fail-open, no hard crash.

Output
- PR diff + test proof in chat.

Done
- Issue done criteria met in `issues/ISSUE-CP-0001-skills-catalog-fetch-cache-fallback.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-2
Objective
- Implement ISSUE-CP-0002.

Constraints
- Keep policy deterministic and log every fail-open event.

Output
- PR diff + policy tests.

Done
- Issue done criteria met in `issues/ISSUE-CP-0002-policy-engine-curated-fail-open.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-3
Objective
- Implement ISSUE-CP-0003.

Constraints
- Must support dry_run and idempotent rerun.

Output
- PR diff + rerun proof logs.

Done
- Issue done criteria met in `issues/ISSUE-CP-0003-installer-wrapper-idempotence.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-4 (Wave 2)
Objective
- Implement ISSUE-CP-0004 after Wave 1 unlock.

Constraints
- Deterministic output required.

Output
- PR diff + deterministic test output.

Done
- Issue done criteria met in `issues/ISSUE-CP-0004-memory-index-generator-v2.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-5 (Wave 2)
Objective
- Implement ISSUE-CP-0005 after Wave 1 unlock.

Constraints
- MCP payload must stay backwards-friendly.

Output
- PR diff + MCP verification logs.

Done
- Issue done criteria met in `issues/ISSUE-CP-0005-mcp-tools-skills-catalog-sync.md`.

Report back
- Post message with Now/Next/Blockers.
