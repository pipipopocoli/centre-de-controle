#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
AUTO_MODE_SCRIPT = ROOT_DIR / "scripts" / "auto_mode.py"
HEALTHCHECK_SCRIPT = ROOT_DIR / "scripts" / "auto_mode_healthcheck.py"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)


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


def _parse_healthcheck_payload(stdout: str) -> dict:
    blob = stdout.strip().split("\nauto_mode_healthcheck", 1)[0]
    return json.loads(blob)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"

        pulse_cmd = [
            sys.executable,
            str(AUTO_MODE_SCRIPT),
            "--project",
            project_id,
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
        check_cmd = [
            sys.executable,
            str(HEALTHCHECK_SCRIPT),
            "--project",
            project_id,
            "--data-dir",
            str(projects_root),
            "--stale-seconds",
            "3600",
            "--max-open",
            "3",
            "--max-snapshot-age-seconds",
            "2100",
        ]

        pulse_1 = _run(pulse_cmd)
        assert pulse_1.returncode == 0, pulse_1.stderr or pulse_1.stdout
        assert "KPI snapshot emitted=true" in pulse_1.stdout, pulse_1.stdout

        snapshot_path = projects_root / project_id / "runs" / "kpi_snapshots.ndjson"
        assert snapshot_path.exists(), "kpi_snapshots.ndjson should be created on first cadence pulse"
        rows_after_first = _read_ndjson(snapshot_path)
        assert len(rows_after_first) == 1, rows_after_first

        check_1 = _run(check_cmd)
        payload_1 = _parse_healthcheck_payload(check_1.stdout)
        assert check_1.returncode == 0, payload_1
        assert payload_1["status"] == "healthy", payload_1
        assert payload_1["issues"] == [], payload_1

        pulse_2 = _run(pulse_cmd)
        assert pulse_2.returncode == 0, pulse_2.stderr or pulse_2.stdout
        assert "KPI snapshot emitted=false reason=min_interval" in pulse_2.stdout, pulse_2.stdout
        rows_after_second = _read_ndjson(snapshot_path)
        assert len(rows_after_second) == 1, rows_after_second

        check_2 = _run(check_cmd)
        payload_2 = _parse_healthcheck_payload(check_2.stdout)
        assert check_2.returncode == 0, payload_2
        assert payload_2["status"] == "healthy", payload_2
        assert payload_2["issues"] == payload_1["issues"] == [], (payload_1, payload_2)
        assert payload_2["max_snapshot_age_seconds"] == 2100, payload_2

    print("OK: wave09 dual-root cadence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
