Mission ID: W20R-A20
Role: @agent-20
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a20_backlog.md

2) Required skills (must load before coding)
- test-master
- playwright
- agentic-coach
- flow-coach

3) File scope (strict allowlist)
- tests/take_ui_screenshots.py
- tests/verify_ui_*.py
- tests/verify_vulgarisation_*.py
- tests/verify_memory_*.py
- tests/verify_wave19_wizard_live_apply_output.py
- tests/verify_takeover_wizard_prompt.py
- tests/verify_takeover_wizard_output_apply.py
- tests/verify_wave19_wizard_live_context_bridge.py
- tests/repro_*.py
- tests/verify_agent_status_model_v4.py
- brainfs/**
- site/**
- tools/**
- docs/swarm_results/wave20_*

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: UI/product tests + policy/config + closeout coordination
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 tests/take_ui_screenshots.py
- python3 tests/verify_ui_pixel_view_tab.py
- python3 tests/verify_vulgarisation_mode_split.py
- python3 tests/verify_memory_compaction.py

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a20_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent20_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
