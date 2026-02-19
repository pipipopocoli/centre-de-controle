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
from app.services.auto_mode import AutoModeAction, dispatch_once  # noqa: E402
from app.services.codex_runner import RunnerResult as CodexRunnerResult  # noqa: E402
from app.services.execution_router import route_action  # noqa: E402


def _append(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def test_dispatch_transports_policy_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"
        _append(
            requests_path,
            {
                "request_id": "req_transport",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "source": "mention",
                "created_at": now,
                "action_scope": "full_access",
                "approval_ref": "APR-200",
                "requested_skills": ["openai-docs", "skill-installer"],
                "message": {
                    "author": "operator",
                    "text": "@agent-1 execute",
                    "mentions": ["agent-1"],
                },
            },
        )
        dispatched = dispatch_once(projects_root, project_id, max_actions=1)
        assert len(dispatched.actions) == 1
        action = dispatched.actions[0]
        assert action.action_scope == "full_access"
        assert action.approval_ref == "APR-200"
        assert action.requested_skills == ["openai-docs", "skill-installer"]
    print("[PASS] dispatch transports policy fields")


def test_policy_denied_is_parity_consistent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        codex_action = AutoModeAction(
            request_id="req_denied_codex",
            project_id=project_id,
            agent_id="agent-1",
            platform="codex",
            execution_mode="codex_headless",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\ndeny",
            app_to_open="Codex",
            notify_text="",
            action_scope="full_access",
            approval_ref=None,
            requested_skills=["openai-docs"],
        )
        ag_action = AutoModeAction(
            request_id="req_denied_ag",
            project_id=project_id,
            agent_id="agent-2",
            platform="antigravity",
            execution_mode="antigravity_supervised",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\ndeny",
            app_to_open="Antigravity",
            notify_text="",
            action_scope="full_access",
            approval_ref=None,
            requested_skills=["openai-docs"],
        )

        codex_res = route_action(codex_action, project_id, projects_root=projects_root, settings={})
        ag_res = route_action(ag_action, project_id, projects_root=projects_root, settings={})
        assert codex_res.status == "policy_denied"
        assert ag_res.status == "policy_denied"
        assert codex_res.error == "approval_ref_required"
        assert ag_res.error == "approval_ref_required"
    print("[PASS] policy deny parity codex/antigravity")


def test_policy_allow_with_approval_ref() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        codex_ok = CodexRunnerResult(
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
        ag_ok = AgRunnerResult(
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
        codex_failed = CodexRunnerResult(
            runner="codex",
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

        codex_action = AutoModeAction(
            request_id="req_allow_codex",
            project_id=project_id,
            agent_id="agent-1",
            platform="codex",
            execution_mode="codex_headless",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\nallow",
            app_to_open="Codex",
            notify_text="",
            action_scope="full_access",
            approval_ref="APR-210",
            requested_skills=["openai-docs"],
        )
        ag_action = AutoModeAction(
            request_id="req_allow_ag",
            project_id=project_id,
            agent_id="agent-2",
            platform="antigravity",
            execution_mode="antigravity_supervised",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\nallow",
            app_to_open="Antigravity",
            notify_text="",
            action_scope="full_access",
            approval_ref="APR-211",
            requested_skills=["openai-docs"],
        )

        with patch("app.services.execution_router.run_codex", return_value=codex_ok):
            codex_res = route_action(codex_action, project_id, projects_root=projects_root, settings={})
            assert codex_res.status == "completed"
        with patch("app.services.execution_router.run_codex", return_value=codex_failed), patch(
            "app.services.execution_router.launch_chat", return_value=ag_ok
        ):
            ag_res = route_action(ag_action, project_id, projects_root=projects_root, settings={})
            assert ag_res.status == "launched"
    print("[PASS] policy allow with approval_ref")


def main() -> int:
    tests = [
        test_dispatch_transports_policy_fields,
        test_policy_denied_is_parity_consistent,
        test_policy_allow_with_approval_ref,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {test.__name__}: {exc}")
            failed += 1

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: runtime conformance L2 verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
