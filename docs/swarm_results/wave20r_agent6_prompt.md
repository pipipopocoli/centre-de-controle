Mission ID: W20R-A6
Role: @agent-6
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a6_backlog.md

2) Required skills (must load before coding)
- typescript-pro
- game-developer
- test-master

3) File scope (strict allowlist)
- apps/cockpit-next-desktop/src/office/editor/**
- apps/cockpit-next-desktop/src/office/engine/**
- apps/cockpit-next-desktop/src/office/layout/**
- apps/cockpit-next-desktop/src/office/types.ts

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Office logic, pathfinding, editor safety/perf
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- npm --prefix apps/cockpit-next-desktop run lint
- npm --prefix apps/cockpit-next-desktop run build

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a6_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent6_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
