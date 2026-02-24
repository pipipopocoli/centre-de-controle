#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
HEALTHCHECK_SCRIPT = ROOT_DIR / "scripts" / "auto_mode_healthcheck.py"
AUTO_MODE_SCRIPT = ROOT_DIR / "scripts" / "auto_mode.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_healthcheck(
    projects_root: Path,
    *,
    max_open: int,
    stale_seconds: int = 3600,
    max_snapshot_age_seconds: int | None = None,
    autopulse_guard: bool = False,
    autopulse_min_interval_minutes: int | None = None,
) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        str(HEALTHCHECK_SCRIPT),
        "--project",
        "cockpit",
        "--data-dir",
        str(projects_root),
        "--stale-seconds",
        str(stale_seconds),
        "--max-open",
        str(max_open),
    ]
    if max_snapshot_age_seconds is not None:
        cmd.extend(["--max-snapshot-age-seconds", str(max_snapshot_age_seconds)])
    if autopulse_guard:
        cmd.append("--autopulse-guard")
    if autopulse_min_interval_minutes is not None:
        cmd.extend(["--autopulse-min-interval-minutes", str(autopulse_min_interval_minutes)])
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    output = proc.stdout.strip()
    json_blob = output.split("\nauto_mode_healthcheck", 1)[0]
    payload = json.loads(json_blob)
    return proc.returncode, payload


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_dir = projects_root / "cockpit"
        runs_dir = project_dir / "runs"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        old_tick = (now - timedelta(hours=10)).replace(microsecond=0).isoformat()
        recent_dispatch = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat()

        # Runtime has one internal request (@clems) and one external (@victor).
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_clems": {
                        "request_id": "req_clems",
                        "project_id": "cockpit",
                        "agent_id": "clems",
                        "status": "queued",
                        "created_at": now.isoformat(),
                    },
                    "req_victor": {
                        "request_id": "req_victor",
                        "project_id": "cockpit",
                        "agent_id": "victor",
                        "status": "queued",
                        "created_at": now.isoformat(),
                    },
                },
                "counters": {
                    "last_tick_at": old_tick,
                    "dispatch_last_at": recent_dispatch,
                },
                "updated_at": old_tick,
            },
        )
        # Ledger is authoritative and matches runtime.
        (runs_dir / "requests.ndjson").write_text(
            json.dumps(
                {
                    "request_id": "req_clems",
                    "project_id": "cockpit",
                    "agent_id": "clems",
                    "status": "queued",
                    "created_at": now.isoformat(),
                }
            )
            + "\n"
            + json.dumps(
                {
                    "request_id": "req_victor",
                    "project_id": "cockpit",
                    "agent_id": "victor",
                    "status": "queued",
                    "created_at": now.isoformat(),
                }
            )
            + "\n",
            encoding="utf-8",
        )

        code, payload = _run_healthcheck(projects_root, max_open=1)
        assert code == 0, payload
        assert payload["status"] == "healthy", payload
        assert payload["open_requests"] == 1, payload
        assert payload["open_requests_total"] == 2, payload
        assert payload["tick_age_seconds"] <= 3600, payload
        assert "stale_tick" not in payload["issues"], payload
        assert payload["issue_details"] == {}, payload
        assert payload["max_snapshot_age_seconds"] == 2100, payload
        assert payload["autopulse_guard_enabled"] is False, payload
        guard_default = payload.get("autopulse_guard_result") or {}
        assert guard_default.get("attempted") is False, payload
        assert guard_default.get("reason") == "disabled", payload

        # Low close-rate alone should not degrade when queue is already under control.
        runtime_requests = {
            "req_open": {
                "request_id": "req_open",
                "project_id": "cockpit",
                "agent_id": "victor",
                "status": "queued",
                "created_at": now.isoformat(),
                "dispatched_at": now.isoformat(),
            }
        }
        for idx in range(6):
            rid = f"req_closed_{idx}"
            runtime_requests[rid] = {
                "request_id": rid,
                "project_id": "cockpit",
                "agent_id": "victor",
                "status": "closed",
                "created_at": now.isoformat(),
                "dispatched_at": now.isoformat(),
                "closed_at": now.isoformat(),
                "closed_reason": "stale_timeout_recovery",
            }
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": list(runtime_requests.keys()),
                "requests": runtime_requests,
                "counters": {
                    "last_tick_at": old_tick,
                    "dispatch_last_at": recent_dispatch,
                },
                "updated_at": old_tick,
            },
        )
        (runs_dir / "requests.ndjson").write_text(
            "\n".join(json.dumps(item) for item in runtime_requests.values()) + "\n",
            encoding="utf-8",
        )

        code_close_rate, payload_close_rate = _run_healthcheck(projects_root, max_open=3)
        assert code_close_rate == 0, payload_close_rate
        assert payload_close_rate["status"] == "healthy", payload_close_rate
        assert payload_close_rate["open_requests"] == 1, payload_close_rate
        assert "close_rate_low" not in payload_close_rate["issues"], payload_close_rate

        # Stale snapshot is a separate gate and can be relaxed by CLI threshold.
        stale_snapshot = (now - timedelta(minutes=50)).replace(microsecond=0).isoformat()
        (runs_dir / "kpi_snapshots.ndjson").write_text(
            json.dumps({"generated_at": stale_snapshot}) + "\n",
            encoding="utf-8",
        )
        code_snapshot, payload_snapshot = _run_healthcheck(projects_root, max_open=2)
        assert code_snapshot == 1, payload_snapshot
        assert payload_snapshot["status"] == "degraded", payload_snapshot
        assert "stale_kpi_snapshot" in payload_snapshot["issues"], payload_snapshot
        assert payload_snapshot["issue_details"]["stale_kpi_snapshot"], payload_snapshot
        assert payload_snapshot["max_snapshot_age_seconds"] == 2100, payload_snapshot

        code_snapshot_relaxed, payload_snapshot_relaxed = _run_healthcheck(
            projects_root,
            max_open=2,
            max_snapshot_age_seconds=7200,
        )
        assert code_snapshot_relaxed == 0, payload_snapshot_relaxed
        assert payload_snapshot_relaxed["status"] == "healthy", payload_snapshot_relaxed
        assert "stale_kpi_snapshot" not in payload_snapshot_relaxed["issues"], payload_snapshot_relaxed
        assert payload_snapshot_relaxed["issue_details"] == {}, payload_snapshot_relaxed
        assert payload_snapshot_relaxed["max_snapshot_age_seconds"] == 7200, payload_snapshot_relaxed

        # With a fresh pulse, stale snapshot should be a soft warning, not a degraded blocker.
        pulse_recent = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat()
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_pulse_fresh": {
                        "request_id": "req_pulse_fresh",
                        "project_id": "cockpit",
                        "agent_id": "victor",
                        "status": "queued",
                        "created_at": now.isoformat(),
                    }
                },
                "counters": {
                    "last_tick_at": pulse_recent,
                    "last_pulse_at": pulse_recent,
                    "dispatch_last_at": pulse_recent,
                },
                "updated_at": pulse_recent,
            },
        )
        (runs_dir / "requests.ndjson").write_text(
            json.dumps(
                {
                    "request_id": "req_pulse_fresh",
                    "project_id": "cockpit",
                    "agent_id": "victor",
                    "status": "queued",
                    "created_at": now.isoformat(),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        code_snapshot_soft, payload_snapshot_soft = _run_healthcheck(projects_root, max_open=2)
        assert code_snapshot_soft == 0, payload_snapshot_soft
        assert payload_snapshot_soft["status"] == "healthy", payload_snapshot_soft
        assert "stale_kpi_snapshot" not in payload_snapshot_soft["issues"], payload_snapshot_soft
        assert "stale_kpi_snapshot_soft" in payload_snapshot_soft["warnings"], payload_snapshot_soft

        # Pulse checkpoint semantics: healthy -> stale -> healthy after pulse.
        pulse_now = datetime.now(timezone.utc).replace(microsecond=0)
        stale_iso = (pulse_now - timedelta(seconds=15)).isoformat()
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_pulse": {
                        "request_id": "req_pulse",
                        "project_id": "cockpit",
                        "agent_id": "victor",
                        "status": "queued",
                        "created_at": pulse_now.isoformat(),
                    }
                },
                "counters": {
                    "last_tick_at": stale_iso,
                    "last_pulse_at": stale_iso,
                    "dispatch_last_at": stale_iso,
                },
                "updated_at": stale_iso,
            },
        )
        (runs_dir / "requests.ndjson").write_text(
            json.dumps(
                {
                    "request_id": "req_pulse",
                    "project_id": "cockpit",
                    "agent_id": "victor",
                    "status": "queued",
                    "created_at": pulse_now.isoformat(),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (runs_dir / "kpi_snapshots.ndjson").write_text("", encoding="utf-8")

        code_pulse_healthy, payload_pulse_healthy = _run_healthcheck(
            projects_root,
            max_open=2,
            stale_seconds=120,
        )
        assert code_pulse_healthy == 0, payload_pulse_healthy
        assert payload_pulse_healthy["status"] == "healthy", payload_pulse_healthy

        code_pulse_stale, payload_pulse_stale = _run_healthcheck(
            projects_root,
            max_open=2,
            stale_seconds=1,
        )
        assert code_pulse_stale == 1, payload_pulse_stale
        assert payload_pulse_stale["status"] == "degraded", payload_pulse_stale
        assert "pulse_stale" in payload_pulse_stale["issues"], payload_pulse_stale
        assert payload_pulse_stale["issue_details"]["pulse_stale"], payload_pulse_stale

        code_pulse_stale_guard, payload_pulse_stale_guard = _run_healthcheck(
            projects_root,
            max_open=2,
            stale_seconds=1,
            autopulse_guard=True,
        )
        assert code_pulse_stale_guard == 1, payload_pulse_stale_guard
        assert payload_pulse_stale_guard["status"] == "degraded", payload_pulse_stale_guard
        assert payload_pulse_stale_guard["autopulse_guard_enabled"] is True, payload_pulse_stale_guard
        guard_skip = payload_pulse_stale_guard.get("autopulse_guard_result") or {}
        assert guard_skip.get("attempted") is False, payload_pulse_stale_guard
        assert guard_skip.get("reason") == "hard_issues_present", payload_pulse_stale_guard

        pulse_cmd = [
            sys.executable,
            str(AUTO_MODE_SCRIPT),
            "--project",
            "cockpit",
            "--data-dir",
            str(projects_root),
            "--once",
            "--max-actions",
            "0",
            "--no-open",
            "--no-clipboard",
            "--no-notify",
            "--kpi-min-interval-minutes",
            "25",
        ]
        pulse_proc = subprocess.run(
            pulse_cmd,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        assert pulse_proc.returncode == 0, pulse_proc.stdout + pulse_proc.stderr

        code_pulse_recovered, payload_pulse_recovered = _run_healthcheck(
            projects_root,
            max_open=2,
            stale_seconds=1,
        )
        assert code_pulse_recovered == 0, payload_pulse_recovered
        assert payload_pulse_recovered["status"] == "healthy", payload_pulse_recovered
        assert "pulse_stale" not in payload_pulse_recovered["issues"], payload_pulse_recovered
        assert payload_pulse_recovered["issue_details"] == {}, payload_pulse_recovered

        # Increase external pressure and verify degraded threshold still triggers.
        state_payload = json.loads((runs_dir / "auto_mode_state.json").read_text(encoding="utf-8"))
        state_payload["requests"]["req_leo"] = {
            "request_id": "req_leo",
            "project_id": "cockpit",
            "agent_id": "leo",
            "status": "queued",
            "created_at": now.isoformat(),
        }
        _write_json(runs_dir / "auto_mode_state.json", state_payload)
        with (runs_dir / "requests.ndjson").open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "request_id": "req_leo",
                        "project_id": "cockpit",
                        "agent_id": "leo",
                        "status": "queued",
                        "created_at": now.isoformat(),
                    }
                )
                + "\n"
            )

        code2, payload2 = _run_healthcheck(projects_root, max_open=1)
        assert code2 == 1, payload2
        assert payload2["status"] == "degraded", payload2
        assert payload2["open_requests"] == 2, payload2
        assert "too_many_open_requests" in payload2["issues"], payload2
        assert payload2["issue_details"]["too_many_open_requests"], payload2

    print("OK: auto_mode healthcheck parity verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
