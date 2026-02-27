#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
AUTO_MODE_SCRIPT = ROOT_DIR / "scripts" / "auto_mode.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _run_once(projects_root: Path, *, max_actions: int) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(AUTO_MODE_SCRIPT),
        "--project",
        "cockpit",
        "--data-dir",
        str(projects_root),
        "--once",
        "--max-actions",
        str(max_actions),
        "--no-open",
        "--no-clipboard",
        "--no-notify",
    ]
    return subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)


def _find_dispatch_audit(stdout: str) -> str:
    for line in stdout.splitlines():
        text = line.strip()
        if text.startswith("DispatchAudit "):
            return text
    return ""


def _seed_project(projects_root: Path, *, credit_guard_enabled: bool) -> None:
    project_dir = projects_root / "cockpit"
    _write_json(
        project_dir / "settings.json",
        {
            "dispatch": {
                "scoring": {"enabled": False},
                "backpressure": {"enabled": True, "queue_target": 3, "max_actions_hard_cap": 5},
            },
            "credit_guard": {
                "enabled": credit_guard_enabled,
                "max_actions_effective": 1,
            },
            "outage_mode": {
                "codex_only_enabled": True,
                "allowed_platforms": ["codex"],
                "allowed_agents": ["victor"],
            },
        },
    )
    _write_json(
        project_dir / "agents" / "registry.json",
        {
            "victor": {
                "agent_id": "victor",
                "name": "Victor",
                "engine": "CDX",
                "platform": "codex",
                "level": 1,
                "lead_id": "clems",
                "role": "backend_lead",
                "skills": [],
            }
        },
    )
    _append_ndjson(
        project_dir / "runs" / "requests.ndjson",
        {
            "request_id": "req_1",
            "project_id": "cockpit",
            "agent_id": "victor",
            "status": "queued",
            "source": "mention",
            "created_at": "2026-02-24T00:00:00+00:00",
            "message": {"text": "Ping @victor"},
        },
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_enabled:
        root_enabled = Path(tmp_enabled) / "projects"
        _seed_project(root_enabled, credit_guard_enabled=True)
        proc_enabled = _run_once(root_enabled, max_actions=5)
        assert proc_enabled.returncode == 0, proc_enabled.stdout + proc_enabled.stderr
        line_enabled = _find_dispatch_audit(proc_enabled.stdout)
        assert line_enabled, proc_enabled.stdout
        assert "credit_guard_enabled=true" in line_enabled, line_enabled
        assert "max_actions_requested=5" in line_enabled, line_enabled
        assert "max_actions_effective=1" in line_enabled, line_enabled
        assert "credit_guard_reason=credit_guard_cap_applied" in line_enabled, line_enabled

    with tempfile.TemporaryDirectory() as tmp_disabled:
        root_disabled = Path(tmp_disabled) / "projects"
        _seed_project(root_disabled, credit_guard_enabled=False)
        proc_disabled = _run_once(root_disabled, max_actions=5)
        assert proc_disabled.returncode == 0, proc_disabled.stdout + proc_disabled.stderr
        line_disabled = _find_dispatch_audit(proc_disabled.stdout)
        assert line_disabled, proc_disabled.stdout
        assert "credit_guard_enabled=false" in line_disabled, line_disabled
        assert "max_actions_requested=5" in line_disabled, line_disabled
        assert "max_actions_effective=5" in line_disabled, line_disabled
        assert "credit_guard_reason=credit_guard_disabled" in line_disabled, line_disabled

    print("OK: wave16 credit guard audit verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
