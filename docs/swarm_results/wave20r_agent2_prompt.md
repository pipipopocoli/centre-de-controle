Mission ID: W20R-A2
Role: @agent-2
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a2_backlog.md

2) Required skills (must load before coding)
- python-pro
- debugging-wizard
- test-master

3) File scope (strict allowlist)
- app/services/chat_parser.py
- app/services/memory_index.py
- app/services/task_planner.py
- app/services/timeline_feed.py
- app/ui/popups.py
- app/ui/project_timeline.py

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Parser/memory/timeline correctness and typing
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 -m py_compile app/services/chat_parser.py app/services/memory_index.py app/services/task_planner.py app/services/timeline_feed.py app/ui/popups.py app/ui/project_timeline.py
- python3 tests/verify_timeline_feed.py
- python3 tests/verify_hybrid_timeline.py

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a2_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent2_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
