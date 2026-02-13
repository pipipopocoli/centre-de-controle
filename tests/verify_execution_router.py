from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.antigravity_runner import RunnerResult as AgRunnerResult  # noqa: E402
from app.services.auto_mode import AutoModeAction, dispatch_once, load_runtime_state  # noqa: E402
from app.services.codex_runner import RunnerResult as CodexRunnerResult  # noqa: E402
from app.services.execution_router import route_action  # noqa: E402


def _append(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"

        _append(
            requests_path,
            {
                "request_id": "req_codex",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "source": "mention",
                "created_at": now,
                "message": {"author": "operator", "text": "@agent-1 do codex", "mentions": ["agent-1"]},
            },
        )
        _append(
            requests_path,
            {
                "request_id": "req_ag",
                "project_id": project_id,
                "agent_id": "agent-2",
                "status": "queued",
                "source": "mention",
                "created_at": now,
                "message": {"author": "operator", "text": "@agent-2 do ag", "mentions": ["agent-2"]},
            },
        )

        dispatched = dispatch_once(projects_root, project_id, max_actions=2)
        assert len(dispatched.actions) == 2
        codex_action = next(item for item in dispatched.actions if item.agent_id == "agent-1")
        ag_action = next(item for item in dispatched.actions if item.agent_id == "agent-2")

        codex_result = CodexRunnerResult(
            runner="codex",
            status="completed",
            success=True,
            launched=True,
            completed=True,
            returncode=0,
            stdout="ok",
            stderr="",
            error=None,
            started_at=now,
            finished_at=now,
            duration_seconds=0.1,
            output_path=None,
            output_text="done",
        )
        with patch("app.services.execution_router.run_codex", return_value=codex_result):
            res = route_action(codex_action, project_id, projects_root=projects_root, settings={})
            assert res.closed is True
            assert res.runner == "codex"

        ag_result = AgRunnerResult(
            runner="antigravity",
            status="launched",
            success=True,
            launched=True,
            completed=False,
            returncode=0,
            stdout="",
            stderr="",
            error=None,
            started_at=now,
            finished_at=now,
            duration_seconds=0.1,
            command=["antigravity", "chat"],
        )
        with patch("app.services.execution_router.launch_chat", return_value=ag_result):
            res = route_action(ag_action, project_id, projects_root=projects_root, settings={})
            assert res.closed is False
            assert res.runner == "antigravity"

        bad_lock_action = AutoModeAction(
            request_id="req_bad_lock",
            project_id=project_id,
            agent_id="agent-1",
            platform="codex",
            execution_mode="codex_headless",
            prompt_text="Project: cockpit\nTask:\nbad lock",
            app_to_open="Codex",
            notify_text="",
        )
        lock_res = route_action(bad_lock_action, project_id, projects_root=projects_root, settings={})
        assert lock_res.status == "project_lock_rejected"

        runtime = load_runtime_state(projects_root, project_id)
        codex_req = runtime["requests"]["req_codex"]
        assert codex_req.get("status") == "closed"
        assert codex_req.get("closed_reason") == "runner_completed"
        assert codex_req.get("completion_source") == "codex_exec"

        ag_req = runtime["requests"]["req_ag"]
        assert ag_req.get("status") == "dispatched"
        assert ag_req.get("completion_source") == "launched_supervised"

        counters = runtime["counters"]
        assert int(counters.get("runner_codex_success") or 0) >= 1
        assert int(counters.get("runner_ag_launch") or 0) >= 1
        assert int(counters.get("runner_ag_pending") or 0) >= 1
        assert runtime["requests"]["req_bad_lock"]["completion_source"] == "project_lock_rejected"

    print("OK: execution router verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
