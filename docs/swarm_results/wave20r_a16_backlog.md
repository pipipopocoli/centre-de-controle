# Wave20R A16 Backlog

- Mission: Launch/automation scripts portability and safety
- Scope allowlist: scripts/auto_mode.py, scripts/auto_mode_core.py, scripts/dispatcher.py, scripts/auto_mode_healthcheck.py, scripts/run_cockpit_next_tauri.sh, launch_cockpit.sh, launch_cockpit_legacy.sh
- Source trackers: docs/swarm_results/wave1_p0p1_tracker.md, docs/swarm_results/wave2_p2_tracker.md, docs/swarm_results/wave2_p3_tracker.md, docs/swarm_results/wave20_unassigned_backlog.md
- Initial rows: 7

| issue_id | source | severity | file | status_before | action | evidence_command | evidence_result | reason_code | note |
|---|---|---|---|---|---|---|---|---|---|
| `ISSUE-W2-P2-T3-022` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `launch_cockpit_legacy.sh` | `defer` | `defer` | `bash -n launch_cockpit_legacy.sh` | `Syntax OK` | `intentional_contract` | Legacy venv launcher maintains backward compatibility; local Python execution is intentional design |
| `ISSUE-W2-P2-T3-033` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `scripts/run_cockpit_next_tauri.sh` | `defer` | `defer` | `bash -n scripts/run_cockpit_next_tauri.sh` | `Syntax OK` | `intentional_contract` | Tauri dev runner requires local cargo/npm; development workflow contract |
| `ISSUE-W2-P2-T3-094` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `scripts/run_cockpit_next_tauri.sh` | `defer` | `defer` | `bash -n scripts/run_cockpit_next_tauri.sh` | `Syntax OK` | `intentional_contract` | Port check fallback to Python3 is intentional portability design |
| `ISSUE-W2-P3-T3-063` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `launch_cockpit_legacy.sh` | `defer` | `defer` | `bash -n launch_cockpit_legacy.sh` | `Syntax OK` | `intentional_contract` | Venv path resolution priority (venv/.venv) is intentional |
| `ISSUE-W2-P3-T3-064` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `launch_cockpit_legacy.sh` | `defer` | `defer` | `bash -n launch_cockpit_legacy.sh` | `Syntax OK` | `intentional_contract` | COCKPIT_DATA_DIR default to 'app' is intentional contract |
| `ISSUE-W2-P3-T3-065` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `launch_cockpit_legacy.sh` | `defer` | `defer` | `bash -n launch_cockpit_legacy.sh` | `Syntax OK` | `intentional_contract` | Strict set -euo pipefail safety mode enabled by design |
| `ISSUE-W2-P3-T3-072` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `scripts/run_cockpit_next_tauri.sh` | `defer` | `defer` | `bash -n scripts/run_cockpit_next_tauri.sh` | `Syntax OK` | `intentional_contract` | Cleanup trap for API_PID is intentional safety design |
