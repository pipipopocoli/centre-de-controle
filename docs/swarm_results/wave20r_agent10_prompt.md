Mission ID: W20R-A10
Role: @agent-10
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a10_backlog.md

2) Required skills (must load before coding)
- rust-engineer
- debugging-wizard
- sre-engineer

3) File scope (strict allowlist)
- crates/cockpit-core/src/storage.rs
- crates/cockpit-core/src/state.rs
- crates/cockpit-core/src/main.rs
- crates/cockpit-core/src/terminal.rs
- crates/cockpit-core/src/lib.rs

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Local runtime robustness and process/session lifecycle
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- cargo check --manifest-path crates/cockpit-core/Cargo.toml
- cargo check --manifest-path apps/cockpit-next-desktop/src-tauri/Cargo.toml

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a10_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent10_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
