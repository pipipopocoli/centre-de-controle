Mission ID: W20R-A13
Role: @agent-13
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a13_backlog.md

2) Required skills (must load before coding)
- code-documenter
- spec-miner
- doc

3) File scope (strict allowlist)
- docs/COCKPIT_NEXT_RUNBOOK.md
- docs/CLOUD_API_PROTOCOL.md
- docs/OPENROUTER_SETUP.md
- docs/WIZARD_LIVE.md
- docs/TAKEOVER_WIZARD.md
- docs/AUTO_MODE.md
- docs/DISPATCHER.md
- docs/PIXEL_VIEW.md
- docs/PACKAGING.md
- docs/RUNBOOK.md
- docs/ui-research.md
- docs/COCKPIT_NEXT_RELEASE_PROOF_2026-03-03.md

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Core docs alignment with runtime reality
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- rg -n "owner123!" docs/COCKPIT_NEXT_RUNBOOK.md docs/CLOUD_API_PROTOCOL.md docs/OPENROUTER_SETUP.md docs/WIZARD_LIVE.md docs/TAKEOVER_WIZARD.md docs/AUTO_MODE.md docs/DISPATCHER.md docs/PIXEL_VIEW.md docs/PACKAGING.md docs/RUNBOOK.md docs/ui-research.md docs/COCKPIT_NEXT_RELEASE_PROOF_2026-03-03.md

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a13_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent13_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
