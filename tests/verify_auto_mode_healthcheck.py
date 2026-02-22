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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_healthcheck(
    projects_root: Path,
    *,
    max_open: int,
    max_snapshot_age_seconds: int | None = None,
) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        str(HEALTHCHECK_SCRIPT),
        "--project",
        "cockpit",
        "--data-dir",
        str(projects_root),
        "--stale-seconds",
        "3600",
        "--max-open",
        str(max_open),
    ]
    if max_snapshot_age_seconds is not None:
        cmd.extend(["--max-snapshot-age-seconds", str(max_snapshot_age_seconds)])
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
        assert payload["max_snapshot_age_seconds"] == 2100, payload

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
        assert payload_snapshot["max_snapshot_age_seconds"] == 2100, payload_snapshot

        code_snapshot_relaxed, payload_snapshot_relaxed = _run_healthcheck(
            projects_root,
            max_open=2,
            max_snapshot_age_seconds=7200,
        )
        assert code_snapshot_relaxed == 0, payload_snapshot_relaxed
        assert payload_snapshot_relaxed["status"] == "healthy", payload_snapshot_relaxed
        assert "stale_kpi_snapshot" not in payload_snapshot_relaxed["issues"], payload_snapshot_relaxed
        assert payload_snapshot_relaxed["max_snapshot_age_seconds"] == 7200, payload_snapshot_relaxed

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

    print("OK: auto_mode healthcheck parity verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
