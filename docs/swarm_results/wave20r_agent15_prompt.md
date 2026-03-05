Mission ID: W20R-A15
Role: @agent-15
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a15_backlog.md

2) Required skills (must load before coding)
- code-documenter
- doc

3) File scope (strict allowlist)
- docs/reports/CP*.md
- docs/reports/BACKLOG*.md
- docs/reports/agent-2/**
- docs/reports/cp01-ui-qa/**
- docs/reports/v3.7/**
- docs/cockpit_v2_roadmap.html
- docs/cockpit_v2_whitepaper.html

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: CP/BACKLOG/report cleanup
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- rg -n "owner123!" docs/reports/CP*.md docs/reports/BACKLOG*.md docs/reports/agent-2 docs/reports/cp01-ui-qa docs/reports/v3.7

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a15_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent15_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
