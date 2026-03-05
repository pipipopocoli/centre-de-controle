Mission ID: W20R-A19
Role: @agent-19
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a19_backlog.md

2) Required skills (must load before coding)
- test-master
- python-pro
- security-reviewer

3) File scope (strict allowlist)
- tests/verify_cloud_api_*.py
- tests/verify_agentic_orchestrator_*.py
- tests/verify_execution_router.py
- tests/verify_antigravity_runner.py
- tests/verify_wave16_*.py
- tests/verify_mcp_skills_tools.py
- tests/verify_project_bible.py
- tests/verify_gatekeeper_eval_integration.py
- tests/verify_auto_mode.py
- tests/verify_live_activity_feed.py
- tests/verify_hybrid_timeline.py
- tests/verify_timeline_feed.py
- tests/verify_agent_registry.py
- tests/verify_wave07_queue_recovery.py
- tests/verify_wave1_security_guards.py

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Runtime/API test modernization
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 tests/verify_wave1_security_guards.py
- python3 tests/verify_execution_router.py
- python3 tests/verify_hybrid_timeline.py
- python3 tests/verify_live_activity_feed.py

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a19_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent19_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
