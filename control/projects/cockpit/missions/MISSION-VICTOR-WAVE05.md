# Mission - Clems to Victor - Wave05 Backend Core

Objective
- Close Wave05 backend core: registry runtime, scoring dispatch, tiered fallback, and cost telemetry backbone.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/data/store.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/agent_registry.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/ollama_runner.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json
- /Users/oliviercloutier/Desktop/Cockpit/tests/

Scope (Out)
- Tournament assets
- Unrelated UI redesign

Delegation
- @agent-1 owns CP-0026/0027
- @agent-3 owns CP-0028
- @agent-11 owns CP-0031 backend telemetry format review

Done
- Registry-backed dispatch live.
- Deterministic ranking + backpressure cap active.
- Codex -> Antigravity -> Ollama fallback contract active.
- Cost events schema emitted in CAD.
- Status update every 2h: Now / Next / Blockers.
