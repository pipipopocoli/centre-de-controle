from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def _write_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "auto_mode.py"
    python = repo_root / ".venv" / "bin" / "python"

    if not script.exists():
        raise SystemExit("missing scripts/auto_mode.py")
    if not python.exists():
        raise SystemExit("missing .venv/bin/python")

    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"
        config_path = projects_root / project_id / "runs" / "auto_mode_config.json"

        config_payload = {
            "app_map": {"codex": "Codex", "antigravity": "Antigravity"},
            "agent_map": {"agent-1": "codex", "agent-2": "antigravity"},
            "max_actions": 0,
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_payload, indent=2), encoding="utf-8")

        req_1 = {
            "request_id": "runreq_test_001",
            "project_id": project_id,
            "agent_id": "agent-1",
            "status": "queued",
            "source": "mention",
            "created_at": "2026-02-07T00:00:00Z",
            "message": {
                "message_id": "msg_test_001",
                "thread_id": None,
                "author": "operator",
                "text": "Ping @agent-1 test",
                "tags": [],
                "mentions": ["agent-1"],
            },
        }
        req_2 = {
            "request_id": "runreq_test_002",
            "project_id": project_id,
            "agent_id": "agent-2",
            "status": "queued",
            "source": "mention",
            "created_at": "2026-02-07T00:00:05Z",
            "message": {
                "message_id": "msg_test_002",
                "thread_id": None,
                "author": "operator",
                "text": "Ping @agent-2 test",
                "tags": [],
                "mentions": ["agent-2"],
            },
        }
        _write_ndjson(requests_path, req_1)
        _write_ndjson(requests_path, req_2)

        cmd = [
            str(python),
            str(script),
            "--project",
            project_id,
            "--data-dir",
            str(projects_root),
            "--config",
            str(config_path),
            "--once",
            "--no-open",
            "--no-clipboard",
            "--no-notify",
        ]

        subprocess.run(cmd, check=True, cwd=str(repo_root))

        inbox_1 = projects_root / project_id / "runs" / "inbox" / "agent-1.ndjson"
        inbox_2 = projects_root / project_id / "runs" / "inbox" / "agent-2.ndjson"
        state = projects_root / project_id / "runs" / "auto_mode_state.json"

        assert inbox_1.exists(), "agent-1 inbox not created"
        assert inbox_2.exists(), "agent-2 inbox not created"
        assert state.exists(), "state file not created"

        inbox_lines_1 = inbox_1.read_text(encoding="utf-8").splitlines()
        inbox_lines_2 = inbox_2.read_text(encoding="utf-8").splitlines()
        assert len(inbox_lines_1) == 1, f"expected 1 inbox line, got {len(inbox_lines_1)}"
        assert len(inbox_lines_2) == 1, f"expected 1 inbox line, got {len(inbox_lines_2)}"

        # Second run should not duplicate.
        subprocess.run(cmd, check=True, cwd=str(repo_root))
        inbox_lines_1b = inbox_1.read_text(encoding="utf-8").splitlines()
        inbox_lines_2b = inbox_2.read_text(encoding="utf-8").splitlines()
        assert len(inbox_lines_1b) == 1, f"expected dedupe, got {len(inbox_lines_1b)}"
        assert len(inbox_lines_2b) == 1, f"expected dedupe, got {len(inbox_lines_2b)}"

    print("OK: auto-mode runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
