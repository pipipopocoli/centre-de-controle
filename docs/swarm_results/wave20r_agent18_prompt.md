Mission ID: W20R-A18
Role: @agent-18
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a18_backlog.md

2) Required skills (must load before coding)
- python-pro
- code-reviewer
- debugging-wizard

3) File scope (strict allowlist)
- scripts/report_cp0037_agent6.py
- scripts/report_cp0037_agent7.py
- scripts/report_cp0051_agent7.py
- scripts/report_wave06_to_clems.py
- scripts/report_wave09_leo.py
- scripts/reply_as_leo_wave07.py
- scripts/reply_wave07_status.py
- scripts/send_cp01_report.py
- scripts/verify_ui_polish.py
- scripts/packaging/generate_tree_icon.py

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Reports/supplementals closure
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 -m py_compile scripts/report_cp0037_agent6.py scripts/report_cp0037_agent7.py scripts/report_cp0051_agent7.py scripts/report_wave06_to_clems.py scripts/report_wave09_leo.py scripts/reply_as_leo_wave07.py scripts/reply_wave07_status.py scripts/send_cp01_report.py scripts/verify_ui_polish.py scripts/packaging/generate_tree_icon.py

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a18_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent18_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
