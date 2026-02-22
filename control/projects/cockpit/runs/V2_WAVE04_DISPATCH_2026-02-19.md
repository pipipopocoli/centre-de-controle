# V2 Wave04 Dispatch Pack (T0)

## Dispatch order
1. @victor
2. @leo
3. @agent-11
4. @agent-1 and @agent-3 (after @victor ack)
5. @agent-6 and @agent-7 (after @leo ack)

## Lead dispatch

### @victor
Objective
- Lock backend contract lane for Wave04 start readiness.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_skills_tools.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_project_routing_strict.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_compaction.py

Delegation
- @agent-1: MCP contract checks
- @agent-3: deterministic memory checks

Done
- backend tests green
- deterministic proof from 2 consecutive runs
- update every 2h in Now/Next/Blockers

### @leo
Objective
- Lock UI ship evidence lane and finalize CP-0015 delta pack.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/agents_grid.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_EVIDENCE_DELTA_P0.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md

Delegation
- @agent-6: scenario matrix and repro
- @agent-7: screenshots and degraded-state evidence

Done
- evidence pack complete and coherent
- no critical UI regression
- update every 2h in Now/Next/Blockers

### @agent-11
Objective
- Produce cleanup decision note (canonical spec/env/docs) without deleting tournament assets.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_CLEANUP_V2.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md

Done
- one decision-complete note:
  - canonical build spec
  - canonical venv path
  - canonical V2 docs source-of-truth
- explicit exclusions for tournament paths
- update in Now/Next/Blockers

## L2 subtasks

### @agent-1
Objective
- Validate MCP contract lane.

Constraints
- no UI changes
- no tournament edits

Output
- MCP checks report and structured payload validation notes

Done
- tools callable with structured payload
- no routing regression

### @agent-3
Objective
- Validate deterministic memory lane.

Constraints
- no UI changes
- no tournament edits

Output
- deterministic 2-run proof

Done
- same inputs produce byte-identical outputs on 2 runs

### @agent-6
Objective
- Finalize scenario matrix for CP-0015 delta.

Output
- matrix with scenario id -> pass/fail -> repro steps

Done
- full matrix coverage and review by @leo

### @agent-7
Objective
- Finalize screenshot evidence for CP-0015 delta.

Output
- captures mapped to scenario ids, including degraded-state

Done
- every capture mapped
- degraded-state capture included
