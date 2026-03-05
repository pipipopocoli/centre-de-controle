Mission ID: W20R-A21
Role: @agent-21 (Opus gatekeeper)
Model: Opus 4.6
Priority: quality > speed. Fix patch integrity and closeout integrity.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_kimi_runs/20260305_152618/run_report.json
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_control_tower_snapshot.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a21_backlog.md

2) File scope (strict allowlist)
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a21_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a2_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent21_report.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent2_report.md
- app/services/chat_parser.py
- app/services/memory_index.py
- app/services/task_planner.py
- app/services/timeline_feed.py
- app/ui/popups.py
- app/ui/project_timeline.py

3) Forbidden scope
- Any file outside allowlist.
- No destructive git commands.

4) Work target
- Rework all failed/skipped/error lanes from source run report.
- Produce canonical unified diffs that pass git apply --check.
- Fill all A21 backlog rows with done/defer + evidence.
- Keep lane allowlist integrity and runtime OpenRouter-only policy.

5) Validation gates
- python3 -m py_compile app/services/chat_parser.py app/services/memory_index.py app/services/task_planner.py app/services/timeline_feed.py app/ui/popups.py app/ui/project_timeline.py
- python3 tests/verify_hybrid_timeline.py
- python3 tests/verify_timeline_feed.py
- python3 /Users/oliviercloutier/Desktop/Cockpit/scripts/wave20r_control_tower.py --write
- python3 /Users/oliviercloutier/Desktop/Cockpit/scripts/wave20r_control_tower.py --strict --strict-open

6) Deliverables
- Update /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a21_backlog.md
- Write /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent21_report.md
