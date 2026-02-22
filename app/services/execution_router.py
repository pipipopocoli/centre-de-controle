from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.antigravity_runner import launch_chat
from app.services.auto_mode import AutoModeAction, update_request_execution
from app.services.codex_runner import run_codex
from app.services.cost_telemetry import COST_EVENT_SCHEMA_VERSION, validate_cost_event
from app.services.ollama_runner import run_ollama
from app.services.reliability_core import (
    RetryPolicy,
    append_event,
    apply_idempotent_tx,
    deterministic_retry_decision,
    finalize_run_bundle,
    is_retryable_failure,
)
from app.services.skills_governance import PolicyContext, evaluate_policy


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


ROUTER_STATUS_DISABLED = "disabled"
ROUTER_STATUS_SKIPPED_WRONG_PROJECT = "skipped_wrong_project"
ROUTER_STATUS_PROJECT_LOCK_REJECTED = "project_lock_rejected"
ROUTER_STATUS_POLICY_DENIED = "policy_denied"
ROUTER_STATUS_DRY_RUN = "dry_run"
ROUTER_STATUS_FAILED = "failed"
ROUTER_STATUS_COMPLETED = "completed"
ROUTER_STATUS_LAUNCHED = "launched"
ROUTER_STATUS_TIMEOUT = "timeout"

ROUTER_RESULT_STATUS_CONTRACT = frozenset(
    {
        ROUTER_STATUS_DISABLED,
        ROUTER_STATUS_SKIPPED_WRONG_PROJECT,
        ROUTER_STATUS_PROJECT_LOCK_REJECTED,
        ROUTER_STATUS_POLICY_DENIED,
        ROUTER_STATUS_DRY_RUN,
        ROUTER_STATUS_FAILED,
        ROUTER_STATUS_COMPLETED,
        ROUTER_STATUS_LAUNCHED,
        ROUTER_STATUS_TIMEOUT,
    }
)

ROUTER_COMPLETION_SOURCE_PROJECT_LOCK_REJECTED = "project_lock_rejected"
ROUTER_COMPLETION_SOURCE_POLICY_DENIED = "policy_denied"
ROUTER_COMPLETION_SOURCE_CODEX_EXEC = "codex_exec"
ROUTER_COMPLETION_SOURCE_CODEX_EXEC_FAILED = "codex_exec_failed"
ROUTER_COMPLETION_SOURCE_LAUNCHED_SUPERVISED = "launched_supervised"
ROUTER_COMPLETION_SOURCE_AG_LAUNCH_FAILED = "ag_launch_failed"
ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC = "ollama_exec"
ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC_FAILED = "ollama_exec_failed"
ROUTER_COMPLETION_SOURCE_ROUTER_ALL_FAILED = "router_all_failed"

ROUTER_COMPLETION_SOURCE_CONTRACT = frozenset(
    {
        ROUTER_COMPLETION_SOURCE_PROJECT_LOCK_REJECTED,
        ROUTER_COMPLETION_SOURCE_POLICY_DENIED,
        ROUTER_COMPLETION_SOURCE_CODEX_EXEC,
        ROUTER_COMPLETION_SOURCE_CODEX_EXEC_FAILED,
        ROUTER_COMPLETION_SOURCE_LAUNCHED_SUPERVISED,
        ROUTER_COMPLETION_SOURCE_AG_LAUNCH_FAILED,
        ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC,
        ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC_FAILED,
        ROUTER_COMPLETION_SOURCE_ROUTER_ALL_FAILED,
    }
)


def _record_execution_event(
    projects_root: Path,
    project_id: str,
    request_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    try:
        append_event(
            projects_root,
            project_id,
            run_id=request_id,
            event_type=event_type,
            payload=payload,
            trace_id=request_id,
            tx_id=f"{request_id}:event:{event_type}",
        )
    except Exception:
        return


def _update_execution_idempotent(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    run_id: str,
    op_name: str,
    tx_suffix: str,
    kwargs: dict[str, Any],
) -> None:
    tx_id = f"{request_id}:tx:{tx_suffix}"

    def _apply() -> dict[str, Any]:
        return update_request_execution(
            projects_root,
            project_id,
            request_id,
            **kwargs,
        )

    apply_idempotent_tx(
        projects_root,
        project_id,
        tx_id=tx_id,
        run_id=run_id,
        op_name=op_name,
        payload={"request_id": request_id, "kwargs": kwargs},
        apply_fn=_apply,
    )


def _automation_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(settings, dict):
        return {}
    automation = settings.get("automation")
    if isinstance(automation, dict):
        return automation
    return settings


def _providers_order(automation: dict[str, Any], action: AutoModeAction) -> tuple[list[str], bool, str]:
    router = automation.get("router") if isinstance(automation.get("router"), dict) else {}

    raw_order = router.get("providers_order")
    if isinstance(raw_order, list):
        base = [str(item).strip().lower() for item in raw_order if str(item).strip()]
    else:
        base = ["codex", "antigravity", "ollama"]

    cleaned: list[str] = []
    for provider in base:
        if provider not in {"codex", "antigravity", "ollama"}:
            continue
        if provider in cleaned:
            continue
        cleaned.append(provider)
    if not cleaned:
        cleaned = ["codex", "antigravity", "ollama"]

    ollama_enabled = bool(router.get("ollama_enabled", False))
    if not ollama_enabled:
        cleaned = [provider for provider in cleaned if provider != "ollama"]

    model = str(router.get("ollama_model") or "llama3.2").strip() or "llama3.2"
    return cleaned, ollama_enabled, model


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(math.ceil(len(text) / 4.0)))


def _cost_rates(settings: dict[str, Any] | None) -> dict[str, tuple[float, float]]:
    default_rates = {
        "codex": (0.010, 0.030),
        "antigravity": (0.004, 0.010),
        "ollama": (0.0, 0.0),
    }
    if not isinstance(settings, dict):
        return default_rates

    cost = settings.get("cost") if isinstance(settings.get("cost"), dict) else {}
    provider_rates = cost.get("provider_rates_cad_per_1k") if isinstance(cost.get("provider_rates_cad_per_1k"), dict) else {}

    out = dict(default_rates)
    for provider in out:
        cfg = provider_rates.get(provider)
        if not isinstance(cfg, dict):
            continue
        try:
            in_rate = float(cfg.get("input", out[provider][0]))
        except (TypeError, ValueError):
            in_rate = out[provider][0]
        try:
            out_rate = float(cfg.get("output", out[provider][1]))
        except (TypeError, ValueError):
            out_rate = out[provider][1]
        out[provider] = (max(0.0, in_rate), max(0.0, out_rate))
    return out


def _emit_cost_event(
    projects_root: Path,
    project_id: str,
    action: AutoModeAction,
    *,
    provider: str,
    elapsed_ms: int,
    output_text: str,
    settings: dict[str, Any] | None,
) -> str | None:
    rates = _cost_rates(settings)
    in_rate, out_rate = rates.get(provider, (0.0, 0.0))
    cost_cfg = settings.get("cost") if isinstance(settings, dict) and isinstance(settings.get("cost"), dict) else {}

    input_tokens = _estimate_tokens(action.prompt_text)
    output_tokens = _estimate_tokens(output_text)
    cached_tokens = 0

    # Pricing is CAD per 1k tokens in this local estimate model.
    cost_cad_estimate = ((input_tokens * in_rate) + (output_tokens * out_rate) + (cached_tokens * 0.0)) / 1000.0

    event = {
        "schema_version": COST_EVENT_SCHEMA_VERSION,
        "run_id": action.request_id,
        "project_id": project_id,
        "agent_id": action.agent_id,
        "provider": provider,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "cached_tokens": int(cached_tokens),
        "cached_input_tokens": int(cached_tokens),
        "elapsed_ms": int(max(elapsed_ms, 0)),
        "currency": str(cost_cfg.get("currency") or "CAD").strip() or "CAD",
        "cost_cad_estimate": round(float(cost_cad_estimate), 6),
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "ts": time.time(),
    }
    is_valid, reason = validate_cost_event(event, project_id=project_id)
    if not is_valid:
        return reason or "cost_event_invalid"
    try:
        _append_ndjson(projects_root / project_id / "runs" / "cost_events.ndjson", event)
    except Exception:
        return "cost_event_append_failed"
    return None


def _disabled_result(action: AutoModeAction, project_id: str, provider: str, message: str) -> ExecutionResult:
    return ExecutionResult(
        request_id=action.request_id,
        agent_id=action.agent_id,
        project_id=project_id,
        runner=provider,
        execution_mode=action.execution_mode,
        launched=False,
        completed=False,
        closed=False,
        status=ROUTER_STATUS_DISABLED,
        error=message,
    )


def route_action(
    action: AutoModeAction,
    project_id: str,
    *,
    projects_root: Path,
    settings: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> ExecutionResult:
    automation = _automation_settings(settings)
    execution_mode = str(automation.get("execution_mode") or action.execution_mode or "codex_headless_ag_supervised")
    codex_cfg = automation.get("codex") if isinstance(automation.get("codex"), dict) else {}
    ag_cfg = automation.get("antigravity") if isinstance(automation.get("antigravity"), dict) else {}
    timeout_cfg = automation.get("timeouts") if isinstance(automation.get("timeouts"), dict) else {}
    codex_timeout = int(timeout_cfg.get("codex_seconds", 900))
    ollama_timeout = int(timeout_cfg.get("ollama_seconds", 180))

    if action.project_id and action.project_id != project_id:
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="none",
            execution_mode=execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status=ROUTER_STATUS_SKIPPED_WRONG_PROJECT,
            error=f"action project mismatch: {action.project_id} != {project_id}",
        )

    if f"PROJECT LOCK: {project_id}" not in action.prompt_text:
        _update_execution_idempotent(
            projects_root,
            project_id,
            action.request_id,
            run_id=action.request_id,
            op_name="update_request_execution",
            tx_suffix=ROUTER_COMPLETION_SOURCE_PROJECT_LOCK_REJECTED,
            kwargs={
                "agent_id": action.agent_id,
                "execution_mode": execution_mode,
                "runner": "router",
                "launched": False,
                "completed": False,
                "completion_source": ROUTER_COMPLETION_SOURCE_PROJECT_LOCK_REJECTED,
                "close_request": False,
                "error": f"missing project lock for {project_id}",
            },
        )
        _record_execution_event(
            projects_root,
            project_id,
            action.request_id,
            ROUTER_COMPLETION_SOURCE_PROJECT_LOCK_REJECTED,
            {"agent_id": action.agent_id, "project_id": project_id},
        )
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner="router",
            execution_mode=execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status=ROUTER_STATUS_PROJECT_LOCK_REJECTED,
            error=f"missing project lock for {project_id}",
        )

    policy_decision = evaluate_policy(
        PolicyContext(
            project_id=project_id,
            runner=action.platform,
            action_scope=str(action.action_scope or "workspace_only"),
            requested_skills=list(action.requested_skills or []),
            approval_ref=action.approval_ref,
        )
    )
    if not policy_decision.allowed:
        _update_execution_idempotent(
            projects_root,
            project_id,
            action.request_id,
            run_id=action.request_id,
            op_name="update_request_execution",
            tx_suffix=ROUTER_COMPLETION_SOURCE_POLICY_DENIED,
            kwargs={
                "agent_id": action.agent_id,
                "execution_mode": execution_mode,
                "runner": action.platform,
                "launched": False,
                "completed": False,
                "completion_source": ROUTER_COMPLETION_SOURCE_POLICY_DENIED,
                "close_request": False,
                "error": f"policy_denied:{policy_decision.reason_code}",
            },
        )
        _record_execution_event(
            projects_root,
            project_id,
            action.request_id,
            ROUTER_COMPLETION_SOURCE_POLICY_DENIED,
            {
                "agent_id": action.agent_id,
                "reason_code": policy_decision.reason_code,
            },
        )
        return ExecutionResult(
            request_id=action.request_id,
            agent_id=action.agent_id,
            project_id=project_id,
            runner=action.platform,
            execution_mode=execution_mode,
            launched=False,
            completed=False,
            closed=False,
            status=ROUTER_STATUS_POLICY_DENIED,
            error=policy_decision.reason_code,
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
            status=ROUTER_STATUS_DRY_RUN,
            error=None,
        )

    providers, ollama_enabled, ollama_model = _providers_order(automation, action)
    last_error: str | None = None

    for provider in providers:
        started = time.perf_counter()

        if provider == "codex":
            if not bool(codex_cfg.get("enabled", True)):
                last_error = "codex automation disabled"
                continue

            retry_cfg = codex_cfg.get("retry") if isinstance(codex_cfg.get("retry"), dict) else {}
            retry_policy = RetryPolicy(
                max_attempts=max(int(retry_cfg.get("max_attempts", 2)), 1),
                base_backoff_ms=max(int(retry_cfg.get("base_backoff_ms", 200)), 0),
                max_backoff_ms=max(int(retry_cfg.get("max_backoff_ms", 2000)), 0),
                jitter_seed=str(retry_cfg.get("jitter_seed") or action.request_id),
            )

            result = run_codex(action.prompt_text, cwd=projects_root / project_id, timeout_s=codex_timeout)
            attempt = 1
            _record_execution_event(
                projects_root,
                project_id,
                action.request_id,
                "codex_attempt",
                {
                    "attempt": attempt,
                    "status": result.status,
                    "success": result.success,
                    "error": result.error,
                },
            )
            while not result.success and is_retryable_failure(result.status, result.error):
                decision = deterministic_retry_decision(
                    retry_policy,
                    attempt=attempt,
                    request_id=action.request_id,
                    error_kind="timeout" if str(result.status).lower() == "timeout" else "retryable",
                )
                _record_execution_event(
                    projects_root,
                    project_id,
                    action.request_id,
                    "codex_retry_decision",
                    {
                        "attempt": decision.attempt,
                        "state": decision.state,
                        "should_retry": decision.should_retry,
                        "backoff_ms": decision.backoff_ms,
                        "reason": decision.reason,
                    },
                )
                if not decision.should_retry:
                    break
                if decision.backoff_ms > 0:
                    time.sleep(float(decision.backoff_ms) / 1000.0)
                attempt += 1
                result = run_codex(action.prompt_text, cwd=projects_root / project_id, timeout_s=codex_timeout)
                _record_execution_event(
                    projects_root,
                    project_id,
                    action.request_id,
                    "codex_attempt",
                    {
                        "attempt": attempt,
                        "status": result.status,
                        "success": result.success,
                        "error": result.error,
                    },
                )

            close_request = bool(result.success and result.completed)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            cost_emit_error = _emit_cost_event(
                projects_root,
                project_id,
                action,
                provider="codex",
                elapsed_ms=elapsed_ms,
                output_text=str(result.output_text or ""),
                settings=settings,
            )
            if cost_emit_error:
                _record_execution_event(
                    projects_root,
                    project_id,
                    action.request_id,
                    "cost_event_dropped",
                    {"provider": "codex", "reason": cost_emit_error},
                )

            _update_execution_idempotent(
                projects_root,
                project_id,
                action.request_id,
                run_id=action.request_id,
                op_name="update_request_execution",
                tx_suffix=(
                    ROUTER_COMPLETION_SOURCE_CODEX_EXEC
                    if close_request
                    else ROUTER_COMPLETION_SOURCE_CODEX_EXEC_FAILED
                ),
                kwargs={
                    "agent_id": action.agent_id,
                    "execution_mode": "codex_headless",
                    "runner": "codex",
                    "launched": result.launched,
                    "completed": result.completed,
                    "completion_source": (
                        ROUTER_COMPLETION_SOURCE_CODEX_EXEC
                        if close_request
                        else ROUTER_COMPLETION_SOURCE_CODEX_EXEC_FAILED
                    ),
                    "close_request": close_request,
                    "closed_reason": "runner_completed" if close_request else None,
                    "error": result.error,
                    "at": result.finished_at,
                },
            )
            _record_execution_event(
                projects_root,
                project_id,
                action.request_id,
                "codex_execution_result",
                {
                    "attempts": attempt,
                    "status": result.status,
                    "close_request": close_request,
                    "error": result.error,
                },
            )

            if close_request:
                finalize_run_bundle(
                    projects_root,
                    project_id,
                    run_id=action.request_id,
                    input_payload={"prompt_text": action.prompt_text},
                    policy_payload={
                        "action_scope": action.action_scope or "workspace_only",
                        "approval_ref": action.approval_ref,
                        "requested_skills": list(action.requested_skills or []),
                    },
                    tool_calls=[{"runner": "codex", "attempts": attempt, "timeout_s": codex_timeout}],
                    outputs_payload={
                        "status": result.status,
                        "success": result.success,
                        "completed": result.completed,
                        "error": result.error,
                        "output_text": result.output_text,
                    },
                    trace_ids=[action.request_id],
                    verdict="success",
                    tx_id=f"{action.request_id}:bundle:codex_final",
                )
                return ExecutionResult(
                    request_id=action.request_id,
                    agent_id=action.agent_id,
                    project_id=project_id,
                    runner="codex",
                    execution_mode="codex_headless",
                    launched=result.launched,
                    completed=result.completed,
                    closed=True,
                    status=result.status,
                    error=result.error,
                )

            last_error = result.error or "codex execution failed"
            continue

        if provider == "antigravity":
            if not bool(ag_cfg.get("enabled", True)):
                last_error = "antigravity automation disabled"
                continue

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
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            cost_emit_error = _emit_cost_event(
                projects_root,
                project_id,
                action,
                provider="antigravity",
                elapsed_ms=elapsed_ms,
                output_text=str(ag_result.stdout or ""),
                settings=settings,
            )
            if cost_emit_error:
                _record_execution_event(
                    projects_root,
                    project_id,
                    action.request_id,
                    "cost_event_dropped",
                    {"provider": "antigravity", "reason": cost_emit_error},
                )

            _update_execution_idempotent(
                projects_root,
                project_id,
                action.request_id,
                run_id=action.request_id,
                op_name="update_request_execution",
                tx_suffix=(
                    ROUTER_COMPLETION_SOURCE_LAUNCHED_SUPERVISED
                    if ag_result.launched
                    else ROUTER_COMPLETION_SOURCE_AG_LAUNCH_FAILED
                ),
                kwargs={
                    "agent_id": action.agent_id,
                    "execution_mode": "antigravity_supervised",
                    "runner": "antigravity",
                    "launched": ag_result.launched,
                    "completed": False,
                    "completion_source": (
                        ROUTER_COMPLETION_SOURCE_LAUNCHED_SUPERVISED
                        if ag_result.launched
                        else ROUTER_COMPLETION_SOURCE_AG_LAUNCH_FAILED
                    ),
                    "close_request": False,
                    "error": ag_result.error,
                    "at": ag_result.finished_at,
                },
            )
            _record_execution_event(
                projects_root,
                project_id,
                action.request_id,
                "ag_launch_result",
                {
                    "status": ag_result.status,
                    "launched": ag_result.launched,
                    "error": ag_result.error,
                },
            )

            if ag_result.launched:
                return ExecutionResult(
                    request_id=action.request_id,
                    agent_id=action.agent_id,
                    project_id=project_id,
                    runner="antigravity",
                    execution_mode="antigravity_supervised",
                    launched=True,
                    completed=False,
                    closed=False,
                    status=ag_result.status,
                    error=ag_result.error,
                )

            last_error = ag_result.error or "antigravity launch failed"
            continue

        if provider == "ollama":
            if not ollama_enabled:
                last_error = "ollama fallback disabled"
                continue

            ollama_result = run_ollama(
                action.prompt_text,
                cwd=projects_root / project_id,
                timeout_s=ollama_timeout,
                model=ollama_model,
            )
            close_request = bool(ollama_result.success and ollama_result.completed)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            cost_emit_error = _emit_cost_event(
                projects_root,
                project_id,
                action,
                provider="ollama",
                elapsed_ms=elapsed_ms,
                output_text=str(ollama_result.output_text or ""),
                settings=settings,
            )
            if cost_emit_error:
                _record_execution_event(
                    projects_root,
                    project_id,
                    action.request_id,
                    "cost_event_dropped",
                    {"provider": "ollama", "reason": cost_emit_error},
                )

            _update_execution_idempotent(
                projects_root,
                project_id,
                action.request_id,
                run_id=action.request_id,
                op_name="update_request_execution",
                tx_suffix=(
                    ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC
                    if close_request
                    else ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC_FAILED
                ),
                kwargs={
                    "agent_id": action.agent_id,
                    "execution_mode": "ollama_local",
                    "runner": "ollama",
                    "launched": ollama_result.launched,
                    "completed": ollama_result.completed,
                    "completion_source": (
                        ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC
                        if close_request
                        else ROUTER_COMPLETION_SOURCE_OLLAMA_EXEC_FAILED
                    ),
                    "close_request": close_request,
                    "closed_reason": "runner_completed" if close_request else None,
                    "error": ollama_result.error,
                    "at": ollama_result.finished_at,
                },
            )
            _record_execution_event(
                projects_root,
                project_id,
                action.request_id,
                "ollama_execution_result",
                {
                    "status": ollama_result.status,
                    "close_request": close_request,
                    "error": ollama_result.error,
                },
            )

            if close_request:
                return ExecutionResult(
                    request_id=action.request_id,
                    agent_id=action.agent_id,
                    project_id=project_id,
                    runner="ollama",
                    execution_mode="ollama_local",
                    launched=ollama_result.launched,
                    completed=ollama_result.completed,
                    closed=True,
                    status=ollama_result.status,
                    error=ollama_result.error,
                )

            last_error = ollama_result.error or "ollama execution failed"
            continue

    _update_execution_idempotent(
        projects_root,
        project_id,
        action.request_id,
        run_id=action.request_id,
        op_name="update_request_execution",
        tx_suffix=ROUTER_COMPLETION_SOURCE_ROUTER_ALL_FAILED,
        kwargs={
            "agent_id": action.agent_id,
            "execution_mode": execution_mode,
            "runner": "router",
            "launched": False,
            "completed": False,
            "completion_source": ROUTER_COMPLETION_SOURCE_ROUTER_ALL_FAILED,
            "close_request": False,
            "error": last_error or "all providers failed",
        },
    )

    return ExecutionResult(
        request_id=action.request_id,
        agent_id=action.agent_id,
        project_id=project_id,
        runner="router",
        execution_mode=execution_mode,
        launched=False,
        completed=False,
        closed=False,
        status=ROUTER_STATUS_FAILED,
        error=last_error or "all providers failed",
    )
