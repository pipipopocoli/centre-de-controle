#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
AUTO_MODE_SCRIPT = ROOT_DIR / "scripts" / "auto_mode.py"


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _seed_root(projects_root: Path, *, request_count: int) -> None:
    runs_dir = projects_root / "cockpit" / "runs"
    for idx in range(request_count):
        _append_ndjson(
            runs_dir / "requests.ndjson",
            {
                "request_id": f"req_{idx}",
                "project_id": "cockpit",
                "agent_id": "victor",
                "status": "queued",
                "source": "mention",
                "created_at": f"2026-02-24T00:00:{idx:02d}+00:00",
                "message": {"text": "Ping @victor"},
            },
        )


def _run_checkpoint(repo_root: Path, app_root: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(AUTO_MODE_SCRIPT),
        "--project",
        "cockpit",
        "--dual-root-checkpoint",
        "--dual-root-repo-data-dir",
        str(repo_root),
        "--dual-root-app-data-dir",
        str(app_root),
    ]
    return subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)


def _parse_json(stdout: str) -> dict:
    return json.loads(stdout.strip())


def main() -> int:
    # Healthy both roots.
    with tempfile.TemporaryDirectory() as tmp_ok:
        base = Path(tmp_ok)
        repo_root = base / "repo_projects"
        app_root = base / "app_projects"
        _seed_root(repo_root, request_count=1)
        _seed_root(app_root, request_count=1)

        proc_ok = _run_checkpoint(repo_root, app_root)
        assert proc_ok.returncode == 0, proc_ok.stdout + proc_ok.stderr
        payload_ok = _parse_json(proc_ok.stdout)
        assert payload_ok["overall_status"] == "healthy", payload_ok
        assert payload_ok["repo"]["status"] == "healthy", payload_ok
        assert payload_ok["app"]["status"] == "healthy", payload_ok
        assert payload_ok["repo"]["pulse"]["actions_used"] == 0, payload_ok
        assert payload_ok["app"]["pulse"]["actions_used"] == 0, payload_ok
        assert payload_ok["repo"]["health"]["autopulse_guard_enabled"] is True, payload_ok
        assert payload_ok["app"]["health"]["autopulse_guard_enabled"] is True, payload_ok
        assert "checkpoint_at" in payload_ok, payload_ok

    # Degraded if one root fails gate (too many open requests).
    with tempfile.TemporaryDirectory() as tmp_bad:
        base = Path(tmp_bad)
        repo_root = base / "repo_projects"
        app_root = base / "app_projects"
        _seed_root(repo_root, request_count=5)
        _seed_root(app_root, request_count=1)

        proc_bad = _run_checkpoint(repo_root, app_root)
        assert proc_bad.returncode == 1, proc_bad.stdout + proc_bad.stderr
        payload_bad = _parse_json(proc_bad.stdout)
        assert payload_bad["overall_status"] == "degraded", payload_bad
        assert payload_bad["repo"]["status"] == "degraded", payload_bad
        assert "too_many_open_requests" in payload_bad["repo"]["health"]["issues"], payload_bad
        assert payload_bad["app"]["status"] in {"healthy", "degraded"}, payload_bad

    print("OK: wave16 dual-root checkpoint wrapper verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
