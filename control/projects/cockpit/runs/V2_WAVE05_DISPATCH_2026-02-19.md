# V2 Wave05 Dispatch Pack (T0)

## Dispatch order
1. @victor
2. @leo
3. @agent-1 and @agent-3 (after @victor ack)
4. @agent-11 (after @victor ack)
5. @agent-6 and @agent-7 (after @leo ack)

## Lead prompts

### @victor
Objective
- Close Wave05 backend core: registry runtime, scoring dispatch, tiered fallback, cost telemetry backbone.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/data/store.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/agent_registry.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/ollama_runner.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json
- /Users/oliviercloutier/Desktop/Cockpit/tests/

Delegation
- @agent-1 owns CP-0026/0027
- @agent-3 owns CP-0028
- @agent-11 owns CP-0031 backend (cost schema)

Done
- registry-backed dispatch live
- deterministic ranking + backpressure
- codex->ag->ollama fallback contract
- cost events schema live
- report every 2h in Now/Next/Blockers

### @leo
Objective
- Close Wave05 UI lane: SLO + cost visibility and final evidence pack.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Delegation
- @agent-6 scenario matrix + repro
- @agent-7 screenshots + degraded-state + comprehension proof

Done
- SLO verdict visible (GO/HOLD)
- cost panel CAD readable
- QA evidence complete and mapped
- report every 2h in Now/Next/Blockers

## L2 prompts

### @agent-1
Objective
- Implement registry runtime source of truth and platform mapping.
Constraints
- No UI edits.
- No tournament edits.
Output
- CP-0026/0027 code + tests.
Done
- no odd/even engine fallback when registry exists
- fallback to default roster when registry missing
- report Now/Next/Blockers

### @agent-3
Objective
- Implement task scoring + deterministic ranking in dispatch.
Constraints
- No tournament edits.
- Keep deterministic tie-break.
Output
- CP-0028/0029 code + tests.
Done
- same input => same ranking
- backpressure cap enforced
- report Now/Next/Blockers

### @agent-11
Objective
- Implement CAD cost telemetry schema and monthly estimator.
Constraints
- No destructive cleanup.
- No tournament dispatch.
Output
- CP-0031 backend artifacts + docs note.
Done
- cost_events schema validated
- monthly CAD estimator reproducible
- report Now/Next/Blockers

### @agent-6
Objective
- Build SLO/cost QA scenario matrix and repro checklist.
Output
- matrix with pass/fail + repro + expected.
Done
- 100 percent scenario coverage
- report Now/Next/Blockers

### @agent-7
Objective
- Produce screenshot evidence for SLO/cost panel including degraded states.
Output
- captures mapped to scenario ids.
Done
- degraded state included
- report Now/Next/Blockers
