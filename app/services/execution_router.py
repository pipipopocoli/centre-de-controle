from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.antigravity_runner import launch_chat
from app.services.auto_mode import AutoModeAction, update_request_execution
from app.services.codex_runner import run_codex


@dataclass(frozen=True)
class ExecutionResult:
    request_id: str
    agent_id: str
    project_id: str
    runner: str
    execution_mode: str
    launched: bool
    completed: bool
    closed: bool
    status: str
    error: str | None = None


def _automation_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(settings, dict):
        return {}
    automation = settings.get("automation")
    if isinstance(automation, dict):
        return automation
    return settings


def route_action(
    action: AutoModeAction,
    project_id: str,
    *,
    projects_root: Path,
    settings: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> ExecutionResult:
    automation = _automation_settings(settings)
    execution_mode = str(automation.get("execution_mode") or "codex_headless_ag_supervised")
    codex_cfg = automation.get("codex") if isinstance(automation.get("codex"), dict) else {}
    ag_cfg = automation.get("antigravity") if isinstance(automation.get("antigravity"), dict) else {}
    timeout_cfg = automation.get("timeouts") if isinstance(automation.get("timeouts"), dict) else {}
    codex_timeout = int(timeout_cfg.get("codex_seconds", 900))

    if action.project_id != project_id:
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="none",
            execution_mode=execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status="skipped_wrong_project",
            error=f"action project mismatch: {action.project_id} != {project_id}",
        )

    if f"PROJECT LOCK: {project_id}" not in action.prompt_text:
        update_request_execution(
            projects_root,
            project_id,
            action.request_id,
            agent_id=action.agent_id,
            execution_mode=action.execution_mode,
            runner="router",
            launched=False,
            completed=False,
            completion_source="project_lock_rejected",
            close_request=False,
            error=f"missing project lock for {project_id}",
        )
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="router",
            execution_mode=action.execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status="project_lock_rejected",
            error=f"missing project lock for {project_id}",
        )

    if dry_run:
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="dry-run",
            execution_mode=execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status="dry_run",
            error=None,
        )

    if action.platform == "codex":
        if not bool(codex_cfg.get("enabled", True)):
            return ExecutionResult(
                request_id=action.request_id,
                agent_id=action.agent_id,
                project_id=project_id,
                runner="codex",
                execution_mode="codex_headless",
                launched=False,
                completed=False,
                closed=False,
                status="disabled",
                error="codex automation disabled",
            )

        result = run_codex(action.prompt_text, cwd=projects_root / project_id, timeout_s=codex_timeout)
        close_request = bool(result.success and result.completed)
        update_request_execution(
            projects_root,
            project_id,
            action.request_id,
            agent_id=action.agent_id,
            execution_mode="codex_headless",
            runner="codex",
            launched=result.launched,
            completed=result.completed,
            completion_source="codex_exec" if close_request else "codex_exec_failed",
            close_request=close_request,
            closed_reason="runner_completed" if close_request else None,
            error=result.error,
            at=result.finished_at,
        )
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="codex",
            execution_mode="codex_headless",
            launched=result.launched,
            completed=result.completed,
            closed=close_request,
            status=result.status,
            error=result.error,
        )

    if not bool(ag_cfg.get("enabled", True)):
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="antigravity",
            execution_mode="antigravity_supervised",
            launched=False,
            completed=False,
            closed=False,
            status="disabled",
            error="antigravity automation disabled",
        )

    ag_mode = str(ag_cfg.get("mode") or "agent")
    cli_path_value = str(ag_cfg.get("cli_path") or "").strip()
    cli_path = Path(cli_path_value) if cli_path_value else Path(
        "/Applications/Antigravity.app/Contents/Resources/app/bin/antigravity"
    )
    ag_result = launch_chat(
        action.prompt_text,
        cwd=projects_root / project_id,
        mode=ag_mode,
        reuse_window=bool(ag_cfg.get("reuse_window", True)),
        cli_path=cli_path,
    )
    update_request_execution(
        projects_root,
        project_id,
        action.request_id,
        agent_id=action.agent_id,
        execution_mode="antigravity_supervised",
        runner="antigravity",
        launched=ag_result.launched,
        completed=False,
        completion_source="launched_supervised" if ag_result.launched else "launch_failed",
        close_request=False,
        error=ag_result.error,
        at=ag_result.finished_at,
    )
    return ExecutionResult(
        request_id=action.request_id,
        agent_id=action.agent_id,
        project_id=project_id,
        runner="antigravity",
        execution_mode="antigravity_supervised",
        launched=ag_result.launched,
        completed=False,
        closed=False,
        status=ag_result.status,
        error=ag_result.error,
    )
