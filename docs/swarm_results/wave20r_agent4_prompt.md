Mission ID: W20R-A4
Role: @agent-4
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a4_backlog.md

2) Required skills (must load before coding)
- legacy-modernizer
- python-pro
- mcp-developer

3) File scope (strict allowlist)
- app/services/execution_router.py
- app/services/agent_registry.py
- app/services/task_matcher.py
- app/data/store.py
- app/services/wizard_live.py
- app/services/takeover_wizard.py
- app/services/codex_runner.py
- app/services/antigravity_runner.py
- app/schemas/takeover_wizard_output.schema.json

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Provider descope + OpenRouter-only migration on app services
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 -m py_compile app/services/execution_router.py app/services/agent_registry.py app/services/task_matcher.py app/data/store.py app/services/wizard_live.py app/services/takeover_wizard.py app/services/codex_runner.py app/services/antigravity_runner.py
- python3 tests/verify_execution_router.py
- python3 tests/verify_takeover_wizard_output_apply.py

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a4_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent4_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
