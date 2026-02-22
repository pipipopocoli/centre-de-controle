from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.eval_audit import (
    OverrideAuditEntry,
    append_override_audit,
    validate_override_request,
)
from app.services.eval_policy import (
    EvalMetrics,
    OverrideRequest,
    evaluate_release,
    load_threshold_policy,
)

class Gate:
    INTAKE = "INTAKE"      # Valid project ID, Owner, DoD
    TRANSITION = "TRANSITION" # All tasks done, tests pass
    RELIABILITY = "RELIABILITY" # No critical risks
    THROUGHPUT = "THROUGHPUT" # Token budget check (Agent 4)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _evaluate_optional_eval_payload(
    request: dict[str, Any],
    project_context: dict[str, Any] | None,
    *,
    project_id: str,
) -> tuple[bool, str]:
    eval_payload = request.get("eval_payload")
    if eval_payload is None:
        return True, "Gate Passed"
    if not isinstance(eval_payload, dict):
        return False, "eval_payload must be an object when provided"

    metrics_payload = eval_payload.get("metrics")
    if not isinstance(metrics_payload, dict):
        return False, "eval_payload.metrics is required and must be an object"
    metrics = EvalMetrics.from_dict(metrics_payload)

    policy_path: Path | None = None
    policy_path_raw = eval_payload.get("policy_path")
    if isinstance(policy_path_raw, str) and policy_path_raw.strip():
        policy_path = Path(policy_path_raw).expanduser()

    policy = load_threshold_policy(policy_path)

    override: OverrideRequest | None = None
    override_payload = eval_payload.get("override")
    if isinstance(override_payload, dict):
        override = OverrideRequest.from_dict(override_payload)

    verdict = evaluate_release(metrics=metrics, policy=policy, override=override)

    if verdict.verdict == "HARD_FAIL":
        reason = verdict.blocking_reasons[0] if verdict.blocking_reasons else "hard-fail threshold breached"
        return False, f"Eval gate blocked dispatch: {reason}"

    if verdict.verdict == "OVERRIDE_APPROVED":
        if override is None:
            return False, "override verdict returned without override payload"
        is_valid, reason = validate_override_request(override)
        if not is_valid:
            return False, f"override rejected: {reason}"

        if isinstance(project_context, dict):
            projects_root_raw = project_context.get("projects_root")
            if projects_root_raw:
                projects_root = Path(str(projects_root_raw)).expanduser()
                entry = OverrideAuditEntry(
                    run_id=override.run_id,
                    project_id=project_id,
                    actor=override.actor,
                    approval_ref=override.approval_ref,
                    rationale=override.rationale,
                    verdict_before="HARD_FAIL",
                    verdict_after="OVERRIDE_APPROVED",
                    policy_version=verdict.policy_version,
                    created_at=_utc_now_iso(),
                )
                append_override_audit(projects_root, project_id, entry)

        return True, "Gate Passed (OVERRIDE_APPROVED)"

    if verdict.verdict == "SOFT_FAIL":
        reason = verdict.soft_reasons[0] if verdict.soft_reasons else "soft-fail threshold breached"
        return True, f"Gate Passed (SOFT_FAIL: {reason})"

    return True, "Gate Passed (PASS)"


def check_dispatch(
    request: dict[str, Any],
    project_context: dict[str, Any] | None = None
) -> tuple[bool, str]:
    """
    Validates if a request can be dispatched based on gate rules.
    Returns (Passed, Reason/Error).
    """
    # 1. Project Lock Check (Basic sanity)
    project_id = str(request.get("project_id") or "").strip()
    agent_id = str(request.get("agent_id") or "").strip()
    
    if not project_id:
        return False, "Missing project_id"
    if not agent_id:
        return False, "Missing agent_id"

    # 2. Eval Harness gate (optional, backward-compatible).
    try:
        return _evaluate_optional_eval_payload(
            request=request,
            project_context=project_context,
            project_id=project_id,
        )
    except Exception as exc:
        return False, f"Eval gate error: {exc}"


def validate_lock(action_context: dict[str, Any]) -> bool:
    """
    Validates that the action respects the mission router lock.
    """
    # This is a placeholder for future lock validation logic
    return True
