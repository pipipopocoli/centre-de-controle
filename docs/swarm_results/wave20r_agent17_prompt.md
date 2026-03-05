Mission ID: W20R-A17
Role: @agent-17
Model: moonshotai/kimi-k2.5
Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls.
Priority: precision > speed. Root-cause fixes only.

1) Context to read first
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave1_p0p1_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p2_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave2_p3_tracker.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20_unassigned_backlog.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a17_backlog.md

2) Required skills (must load before coding)
- cli-developer
- python-pro
- test-master

3) File scope (strict allowlist)
- scripts/capture_degraded.py
- scripts/export_status_pdf.py
- scripts/generate_timeline_evidence.py
- scripts/import_office_tileset.sh
- scripts/import_pixel_reference_assets.sh
- scripts/release/publish_demo_to_drive.sh
- scripts/update_leo_state.py
- scripts/wizard_live.py

4) Forbidden scope
- Any file outside allowlist.
- No swarm rerun, no destructive git commands.

5) Work rules
- Mission focus: Script hardening + path portability
- Close every row in backlog as done/defer.
- defer requires reason_code in {non_repro, stale, policy, intentional_contract} + reproducible evidence command.
- Fix order: P0/P1 first, then P2 bug/security, then P2/P3 architecture/types/docs/perf.
- Runtime target OpenRouter-only: no active codex/antigravity/ollama execution path.

6) Validation gates
- python3 -m py_compile scripts/capture_degraded.py scripts/export_status_pdf.py scripts/generate_timeline_evidence.py scripts/update_leo_state.py scripts/wizard_live.py
- bash -n scripts/import_office_tileset.sh scripts/import_pixel_reference_assets.sh scripts/release/publish_demo_to_drive.sh

7) Deliverables
- Update: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_a17_backlog.md
- Fill report: /Users/oliviercloutier/Desktop/Cockpit/docs/swarm_results/wave20r_agent17_report.md
- Report includes: summary table, evidence list, residual risks, Now/Next/Blockers.
