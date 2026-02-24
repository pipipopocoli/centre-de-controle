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


def _read_ndjson(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _seed_runtime(
    projects_root: Path,
    *,
    tick_age_seconds: int,
    pulse_age_seconds: int,
    snapshot_age_seconds: int,
) -> tuple[Path, Path, Path]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    project_dir = projects_root / "cockpit"
    runs_dir = project_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    tick_iso = (now - timedelta(seconds=max(tick_age_seconds, 0))).isoformat()
    pulse_iso = (now - timedelta(seconds=max(pulse_age_seconds, 0))).isoformat()
    snapshot_iso = (now - timedelta(seconds=max(snapshot_age_seconds, 0))).isoformat()

    _write_json(
        runs_dir / "auto_mode_state.json",
        {
            "schema_version": 3,
            "processed": [],
            "requests": {
                "req_victor": {
                    "request_id": "req_victor",
                    "project_id": "cockpit",
                    "agent_id": "victor",
                    "status": "queued",
                    "created_at": now.isoformat(),
                }
            },
            "counters": {
                "last_tick_at": tick_iso,
                "last_pulse_at": pulse_iso,
                "dispatch_last_at": tick_iso,
            },
            "updated_at": tick_iso,
        },
    )
    (runs_dir / "requests.ndjson").write_text(
        json.dumps(
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
    (runs_dir / "kpi_snapshots.ndjson").write_text(
        json.dumps({"generated_at": snapshot_iso}) + "\n",
        encoding="utf-8",
    )
    return runs_dir, runs_dir / "kpi_snapshots.ndjson", runs_dir / "auto_mode_state.json"


def _run_healthcheck(
    projects_root: Path,
    *,
    stale_seconds: int,
    max_open: int = 3,
    max_snapshot_age_seconds: int = 2100,
    autopulse_guard: bool = False,
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
        "--max-snapshot-age-seconds",
        str(max_snapshot_age_seconds),
    ]
    if autopulse_guard:
        cmd.append("--autopulse-guard")

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    payload_blob = proc.stdout.strip().split("\nauto_mode_healthcheck", 1)[0]
    payload = json.loads(payload_blob)
    return proc.returncode, payload


def main() -> int:
    # Scenario A: stale snapshot + fresh pulse without guard -> warning only.
    with tempfile.TemporaryDirectory() as tmp_a:
        projects_root_a = Path(tmp_a) / "projects"
        _, snapshot_path_a, _ = _seed_runtime(
            projects_root_a,
            tick_age_seconds=300,
            pulse_age_seconds=300,
            snapshot_age_seconds=3600,
        )
        code_a, payload_a = _run_healthcheck(projects_root_a, stale_seconds=3600, autopulse_guard=False)
        assert code_a == 0, payload_a
        assert payload_a["status"] == "healthy", payload_a
        assert "stale_kpi_snapshot_soft" in payload_a["warnings"], payload_a
        assert payload_a["autopulse_guard_enabled"] is False, payload_a
        guard_a = payload_a.get("autopulse_guard_result") or {}
        assert guard_a.get("attempted") is False, payload_a
        assert guard_a.get("reason") == "disabled", payload_a
        assert len(_read_ndjson(snapshot_path_a)) == 1

    # Scenario B: stale snapshot + fresh pulse with guard -> guard emits fresh snapshot.
    with tempfile.TemporaryDirectory() as tmp_b:
        projects_root_b = Path(tmp_b) / "projects"
        _, snapshot_path_b, _ = _seed_runtime(
            projects_root_b,
            tick_age_seconds=300,
            pulse_age_seconds=300,
            snapshot_age_seconds=3600,
        )
        code_b, payload_b = _run_healthcheck(projects_root_b, stale_seconds=3600, autopulse_guard=True)
        assert code_b == 0, payload_b
        assert payload_b["status"] == "healthy", payload_b
        assert "stale_kpi_snapshot_soft" not in payload_b["warnings"], payload_b
        assert "stale_kpi_snapshot" not in payload_b["issues"], payload_b
        assert payload_b["autopulse_guard_enabled"] is True, payload_b
        guard_b = payload_b.get("autopulse_guard_result") or {}
        assert guard_b.get("attempted") is True, payload_b
        assert guard_b.get("applied") is True, payload_b
        assert guard_b.get("reason") == "snapshot_emitted", payload_b
        assert payload_b.get("snapshot_age_seconds") is not None, payload_b
        assert int(payload_b["snapshot_age_seconds"]) <= 2100, payload_b
        assert len(_read_ndjson(snapshot_path_b)) >= 2

    # Scenario C: hard issue present -> guard is skipped and degraded remains.
    with tempfile.TemporaryDirectory() as tmp_c:
        projects_root_c = Path(tmp_c) / "projects"
        _, snapshot_path_c, _ = _seed_runtime(
            projects_root_c,
            tick_age_seconds=7200,
            pulse_age_seconds=7200,
            snapshot_age_seconds=3600,
        )
        code_c, payload_c = _run_healthcheck(projects_root_c, stale_seconds=60, autopulse_guard=True)
        assert code_c == 1, payload_c
        assert payload_c["status"] == "degraded", payload_c
        assert "pulse_stale" in payload_c["issues"], payload_c
        guard_c = payload_c.get("autopulse_guard_result") or {}
        assert guard_c.get("attempted") is False, payload_c
        assert guard_c.get("reason") == "hard_issues_present", payload_c
        assert len(_read_ndjson(snapshot_path_c)) == 1

    # Pulse-only operator path should run as an explicit no-side-effect pulse command.
    with tempfile.TemporaryDirectory() as tmp_d:
        projects_root_d = Path(tmp_d) / "projects"
        cmd = [
            sys.executable,
            str(AUTO_MODE_SCRIPT),
            "--project",
            "cockpit",
            "--data-dir",
            str(projects_root_d),
            "--pulse-only",
            "--kpi-min-interval-minutes",
            "25",
        ]
        proc_d = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
        assert proc_d.returncode == 0, proc_d.stdout + proc_d.stderr
        assert "KPI snapshot" in proc_d.stdout, proc_d.stdout

    print("OK: wave16 recency autopulse guard verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
