# V2-WAVE-03 Dispatch Pack (6h)

## Lead dispatch

### @victor
Objective
- Close ISSUE-CP-0004 and ISSUE-CP-0005 in this 6h sprint, implementation-first.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0004-memory-index-generator-v2.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0005-mcp-tools-skills-catalog-sync.md
- /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/skills_catalog.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/skills_installer.py

Delegation
- @agent-3 owns CP-0004
- @agent-1 owns CP-0005

Done
- CP-0004 deterministic index generator done + tests
- CP-0005 MCP tools list_skills_catalog + sync_skills (dry_run true/false) callable
- status update every 2h in Now/Next/Blockers

### @leo
Objective
- Close ISSUE-CP-0015 with a complete UI QA evidence pack for checkpoint signoff.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0015-ui-qa-evidence-pack.md
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Delegation
- @agent-6 scenario matrix + repro steps
- @agent-7 screenshots + degraded-state evidence

Done
- evidence pack complete and linked from STATE/ROADMAP
- pass/fail + repro per scenario
- status update every 2h in Now/Next/Blockers

## L2 subtasks

### @agent-3
Objective
- Deliver ISSUE-CP-0004 deterministic memory index generator.

Constraints
- No semantic retrieval expansion.
- Keep output deterministic for identical input.

Output
- implementation + deterministic test proof for CP-0004

Done
- same input => same output across 2 consecutive runs
- report back with Now/Next/Blockers

### @agent-1
Objective
- Deliver ISSUE-CP-0005 MCP tools list_skills_catalog and sync_skills with dry_run support.

Constraints
- No UI work.
- Clear structured errors on missing catalog.

Output
- MCP tool schema + handler + verification proof

Done
- both tools callable
- dry_run true/false behavior explicit
- report back with Now/Next/Blockers

### @agent-6
Objective
- Build QA scenario matrix and repro checklist for CP-0015.

Output
- scenario table with pass/fail fields + reproduction steps

Done
- matrix complete and reviewed by @leo
- report Now/Next/Blockers

### @agent-7
Objective
- Produce screenshot evidence pack including one degraded-state case for CP-0015.

Output
- screenshot set + mapping to scenarios

Done
- each screenshot mapped to scenario id
- degraded-state screenshot included
- report Now/Next/Blockers
