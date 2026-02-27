# Wave17 Runtime Checkpoint

Timestamp (UTC): 2026-02-27T05:39Z
Objective: dual-root recency health + partial AG reopen under credit guard (max_actions_effective=1).

## Commands
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_codex_only_outage_mode.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_recency_autopulse_guard.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_onboarding_contract.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_credit_guard_audit.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_dual_root_checkpoint.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --dual-root-checkpoint
```

## Outputs
```text
OK: wave16 codex-only outage mode verified
OK: wave16 recency autopulse guard verified
OK: wave16 onboarding contract verified
OK: wave16 credit guard audit verified
OK: wave16 dual-root checkpoint wrapper verified
```

Dual-root checkpoint summary:
- `repo`: healthy
- `app`: healthy
- `overall_status`: healthy
- `dispatch_audit`: codex_only_enabled=false, credit_guard_enabled=true, allowed_platforms=[codex,antigravity], allowed_agents=[victor,nova,leo,agent-3]

Dual-root checkpoint JSON (stdout):
```json
{
  "checkpoint_at": "2026-02-27T05:39:48+00:00",
  "project_id": "cockpit",
  "repo": {
    "projects_root": "/Users/oliviercloutier/Desktop/Cockpit/control/projects",
    "pulse": {
      "dispatched": 0,
      "skipped": 59,
      "actions_used": 0,
      "gate_blocked": 0,
      "state_path": "/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/auto_mode_state.json",
      "snapshot": {
        "emitted": false,
        "reason": "min_interval",
        "generated_at": "2026-02-27T05:39:48+00:00",
        "last_generated_at": "2026-02-27T05:38:53+00:00",
        "snapshot_path": "/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/kpi_snapshots.ndjson",
        "min_interval_minutes": 25
      }
    },
    "dispatch_audit": {
      "max_actions_requested": 0,
      "max_actions_effective": 0,
      "credit_guard_enabled": true,
      "codex_only_enabled": false,
      "allowed_platforms": [
        "codex",
        "antigravity"
      ],
      "allowed_agents": [
        "agent-3",
        "leo",
        "nova",
        "victor"
      ],
      "credit_guard_reason": "credit_guard_enabled_no_cap"
    },
    "health": {
      "status": "healthy",
      "project_id": "cockpit",
      "projects_root": "/Users/oliviercloutier/Desktop/Cockpit/control/projects",
      "mode": "runtime_v3",
      "state_path": "/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/auto_mode_state.json",
      "open_requests": 0,
      "open_requests_external": 0,
      "open_external_inflight": 0,
      "open_requests_total": 3,
      "requests_log_open_like": 15,
      "runtime_sync_closed_count": 0,
      "runtime_missing_closed_count": 0,
      "last_tick_at": "2026-02-27T05:39:48+00:00",
      "last_pulse_at": "2026-02-27T05:39:48+00:00",
      "pulse_age_seconds": 0,
      "last_activity_at": "2026-02-27T05:39:48+00:00",
      "tick_age_seconds": 0,
      "snapshot_age_seconds": 55,
      "max_snapshot_age_seconds": 2100,
      "autopulse_guard_enabled": true,
      "autopulse_guard_result": {
        "attempted": false,
        "applied": false,
        "reason": "snapshot_not_stale",
        "snapshot_result": null,
        "hard_issues": []
      },
      "kpi": {
        "computed_at": "2026-02-27T05:39:48+00:00",
        "window_hours": 24,
        "open_external_total": 0,
        "open_reminded_external": 0,
        "dispatched_external_24h": 0,
        "closed_reply_received_24h": 0,
        "reminder_noise_pct": 0.0,
        "close_rate_24h": 0.0
      },
      "min_close_rate": 80.0,
      "min_dispatched_close_rate": 5,
      "kpi_snapshot_path": "/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/kpi_snapshots.ndjson",
      "counters": {
        "ticks": 26,
        "dispatched_total": 18,
        "skipped_total": 222,
        "skipped_invalid": 0,
        "skipped_reminder": 0,
        "skipped_old": 2,
        "skipped_wrong_project": 0,
        "skipped_duplicate": 219,
        "skipped_internal_agent": 1,
        "runner_codex_success": 0,
        "runner_codex_fail": 0,
        "runner_ag_launch": 0,
        "runner_ag_pending": 0,
        "last_tick_at": "2026-02-27T05:39:48+00:00",
        "last_stats": {
          "timestamp": "2026-02-27T05:39:48+00:00",
          "dispatched": 0,
          "skipped": 59,
          "actions_used": 0,
          "gate_blocked": 0
        },
        "reminder_events_total": 8,
        "dispatch_total": 12,
        "agent_total_agent-6": 2,
        "agent_total_agent-7": 1,
        "dispatch_last_count": 0,
        "dispatch_last_at": "2026-02-27T05:39:48+00:00",
        "runtime_log_sync_closed_total": 15,
        "agent_total_nova": 2,
        "agent_total_clems": 5,
        "closed_total": 12,
        "agent_total_leo": 1,
        "agent_total_victor": 1,
        "last_pulse_at": "2026-02-27T05:39:48+00:00"
      },
      "issues": [],
      "issue_details": {},
      "warnings": [],
      "warning_details": {}
    },
    "status": "healthy"
  },
  "app": {
    "projects_root": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects",
    "pulse": {
      "dispatched": 0,
      "skipped": 602,
      "actions_used": 0,
      "gate_blocked": 0,
      "state_path": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/auto_mode_state.json",
      "snapshot": {
        "emitted": false,
        "reason": "min_interval",
        "generated_at": "2026-02-27T05:39:48+00:00",
        "last_generated_at": "2026-02-27T05:38:53+00:00",
        "snapshot_path": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/kpi_snapshots.ndjson",
        "min_interval_minutes": 25
      }
    },
    "dispatch_audit": {
      "max_actions_requested": 0,
      "max_actions_effective": 0,
      "credit_guard_enabled": true,
      "codex_only_enabled": false,
      "allowed_platforms": [
        "codex",
        "antigravity"
      ],
      "allowed_agents": [
        "agent-3",
        "leo",
        "nova",
        "victor"
      ],
      "credit_guard_reason": "credit_guard_enabled_no_cap"
    },
    "health": {
      "status": "healthy",
      "project_id": "cockpit",
      "projects_root": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects",
      "mode": "runtime_v3",
      "state_path": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/auto_mode_state.json",
      "open_requests": 1,
      "open_requests_external": 1,
      "open_external_inflight": 1,
      "open_requests_total": 2,
      "requests_log_open_like": 426,
      "runtime_sync_closed_count": 0,
      "runtime_missing_closed_count": 0,
      "last_tick_at": "2026-02-27T05:39:48+00:00",
      "last_pulse_at": "2026-02-27T05:39:48+00:00",
      "pulse_age_seconds": 0,
      "last_activity_at": "2026-02-27T05:39:48+00:00",
      "tick_age_seconds": 0,
      "snapshot_age_seconds": 55,
      "max_snapshot_age_seconds": 2100,
      "autopulse_guard_enabled": true,
      "autopulse_guard_result": {
        "attempted": false,
        "applied": false,
        "reason": "snapshot_not_stale",
        "snapshot_result": null,
        "hard_issues": []
      },
      "kpi": {
        "computed_at": "2026-02-27T05:39:48+00:00",
        "window_hours": 24,
        "open_external_total": 1,
        "open_reminded_external": 0,
        "dispatched_external_24h": 0,
        "closed_reply_received_24h": 0,
        "reminder_noise_pct": 0.0,
        "close_rate_24h": 0.0
      },
      "min_close_rate": 80.0,
      "min_dispatched_close_rate": 5,
      "kpi_snapshot_path": "/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/kpi_snapshots.ndjson",
      "counters": {
        "ticks": 64,
        "dispatched_total": 10,
        "skipped_total": 13763,
        "skipped_invalid": 0,
        "skipped_reminder": 0,
        "skipped_old": 0,
        "skipped_wrong_project": 11,
        "skipped_duplicate": 13752,
        "skipped_internal_agent": 0,
        "runner_codex_success": 0,
        "runner_codex_fail": 1,
        "runner_ag_launch": 1,
        "runner_ag_pending": 5,
        "last_tick_at": "2026-02-27T05:39:48+00:00",
        "last_stats": {
          "timestamp": "2026-02-27T05:39:48+00:00",
          "dispatched": 0,
          "skipped": 602,
          "actions_used": 0,
          "gate_blocked": 0
        },
        "dispatch_last_count": 0,
        "dispatch_last_at": "2026-02-27T05:39:48+00:00",
        "reminder_events_total": 209,
        "dispatch_total": 10,
        "agent_total_clems": 3,
        "agent_total_nova": 2,
        "agent_total_leo": 2,
        "agent_total_victor": 3,
        "closed_total": 11,
        "queue_exact_dupe_removed_total": 406,
        "last_pulse_at": "2026-02-27T05:39:48+00:00"
      },
      "issues": [],
      "issue_details": {},
      "warnings": [],
      "warning_details": {}
    },
    "status": "healthy"
  },
  "overall_status": "healthy"
}
```

## Now / Next / Blockers
- Now: dual-root checkpoint is healthy (repo+app) and outage_mode now allows AG under credit guard (max_actions_effective=1).
- Next: keep pulse/check cadence every 30-45 minutes; reopen fanout only after 2 consecutive healthy checkpoints.
- Blockers: none.

