from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import AutoModeAction, dispatch_once, load_runtime_state  # noqa: E402
from app.services.openrouter_runner import RunnerResult as OpenRouterRunnerResult  # noqa: E402
from app.services.execution_router import (  # noqa: E402
    ROUTER_COMPLETION_SOURCE_CONTRACT,
    ROUTER_RESULT_STATUS_CONTRACT,
    route_action,
)


def _append(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _read_cost_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


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
                "message": {"author": "operator", "text": "@agent-1 do openrouter", "mentions": ["agent-1"]},
            },
        )
        _append(
            requests_path,
            {
                "request_id": "req_or_2",
                "project_id": project_id,
                "agent_id": "agent-2",
                "status": "queued",
                "source": "mention",
                "created_at": now,
                "message": {"author": "operator", "text": "@agent-2 do openrouter", "mentions": ["agent-2"]},
            },
        )

        dispatched = dispatch_once(projects_root, project_id, max_actions=2)
        assert len(dispatched.actions) == 2
        action_1 = next(item for item in dispatched.actions if item.agent_id == "agent-1")
        action_2 = next(item for item in dispatched.actions if item.agent_id == "agent-2")

        openrouter_result = OpenRouterRunnerResult(
            runner="openrouter",
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
        with patch("app.services.execution_router.run_openrouter", return_value=openrouter_result):
            res = route_action(action_1, project_id, projects_root=projects_root, settings={})
            assert res.closed is True
            assert res.runner == "openrouter"
            assert res.status in ROUTER_RESULT_STATUS_CONTRACT

        openrouter_failed = OpenRouterRunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=True,
            completed=True,
            returncode=1,
            stdout="",
            stderr="failure",
            error="failure",
            started_at=now,
            finished_at=now,
            duration_seconds=0.1,
            output_path=None,
            output_text="",
        )
        with patch("app.services.execution_router.run_openrouter", return_value=openrouter_failed):
            res = route_action(action_2, project_id, projects_root=projects_root, settings={})
            assert res.closed is False
            assert res.runner == "router"
            assert res.status in ROUTER_RESULT_STATUS_CONTRACT

        bad_lock_action = AutoModeAction(
            request_id="req_bad_lock",
            project_id=project_id,
            agent_id="agent-1",
            platform="openrouter",
            execution_mode="openrouter_headless",
            prompt_text="Project: cockpit\nTask:\nbad lock",
            app_to_open="OpenRouter",
            notify_text="",
        )
        lock_res = route_action(bad_lock_action, project_id, projects_root=projects_root, settings={})
        assert lock_res.status == "project_lock_rejected"
        assert lock_res.status in ROUTER_RESULT_STATUS_CONTRACT

        denied_openrouter = AutoModeAction(
            request_id="req_denied_openrouter",
            project_id=project_id,
            agent_id="agent-1",
            platform="openrouter",
            execution_mode="openrouter_headless",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\nfull access",
            app_to_open="OpenRouter",
            notify_text="",
            action_scope="full_access",
            approval_ref=None,
            requested_skills=["openai-docs"],
        )
        denied_openrouter_res = route_action(denied_openrouter, project_id, projects_root=projects_root, settings={})
        assert denied_openrouter_res.status == "policy_denied"
        assert denied_openrouter_res.error == "approval_ref_required"
        assert denied_openrouter_res.status in ROUTER_RESULT_STATUS_CONTRACT

        approved_openrouter = AutoModeAction(
            request_id="req_approved_openrouter",
            project_id=project_id,
            agent_id="agent-1",
            platform="openrouter",
            execution_mode="openrouter_headless",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\napproved full access",
            app_to_open="OpenRouter",
            notify_text="",
            action_scope="full_access",
            approval_ref="APR-001",
            requested_skills=["openai-docs"],
        )
        with patch("app.services.execution_router.run_openrouter", return_value=openrouter_result):
            approved_openrouter_res = route_action(
                approved_openrouter, project_id, projects_root=projects_root, settings={}
            )
            assert approved_openrouter_res.status == "completed"
            assert approved_openrouter_res.status in ROUTER_RESULT_STATUS_CONTRACT

        runtime = load_runtime_state(projects_root, project_id)
        codex_req = runtime["requests"]["req_codex"]
        assert codex_req.get("status") == "closed"
        assert codex_req.get("closed_reason") == "runner_completed"
        assert codex_req.get("completion_source") == "openrouter_exec"

        ag_req = runtime["requests"]["req_or_2"]
        assert ag_req.get("status") == "dispatched"
        assert ag_req.get("completion_source") in {"openrouter_exec_failed", "router_all_failed"}

        counters = runtime["counters"]
        assert int(counters.get("runner_openrouter_success") or 0) >= 1
        assert runtime["requests"]["req_bad_lock"]["completion_source"] == "project_lock_rejected"
        assert runtime["requests"]["req_denied_openrouter"]["completion_source"] == "policy_denied"
        for request_payload in runtime["requests"].values():
            if not isinstance(request_payload, dict):
                continue
            completion_source = str(request_payload.get("completion_source") or "").strip()
            if completion_source:
                assert completion_source in ROUTER_COMPLETION_SOURCE_CONTRACT, (
                    f"unknown completion_source: {completion_source}"
                )

        events = _read_cost_events(projects_root / project_id / "runs" / "cost_events.ndjson")
        req_or_2_providers = [str(item.get("provider") or "") for item in events if item.get("run_id") == "req_or_2"]
        assert req_or_2_providers == ["openrouter"], f"req_or_2 strict order mismatch: {req_or_2_providers}"
        req_approved_or_providers = [
            str(item.get("provider") or "") for item in events if item.get("run_id") == "req_approved_openrouter"
        ]
        assert req_approved_or_providers == ["openrouter"], (
            f"req_approved_openrouter strict order mismatch: {req_approved_or_providers}"
        )

    print("OK: execution router verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
