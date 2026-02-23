from __future__ import annotations

import re
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


MISSION_CRITICAL_TRIGGER_ALL_FULL_ACCESS = "all_full_access"
MISSION_CRITICAL_DEFAULT_APPROVAL_REF_PATTERN = r"^APR-[A-Za-z0-9._-]+$"
MISSION_CRITICAL_DEFAULT_REQUIRED_EVIDENCE_SECTIONS = ("tests", "screenshots", "logs", "docs_updates")

MISSION_CRITICAL_GATE_CODE_PASSED = "passed"
MISSION_CRITICAL_GATE_CODE_NOT_APPLICABLE = "not_applicable"
MISSION_CRITICAL_GATE_CODE_DISABLED = "gate_disabled"
MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING = "approval_ref_missing"
MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_INVALID = "approval_ref_invalid"
MISSION_CRITICAL_GATE_CODE_EVIDENCE_PAYLOAD_INVALID = "evidence_payload_invalid"
MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_MISSING = "evidence_section_missing"
MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_EMPTY = "evidence_section_empty"
MISSION_CRITICAL_GATE_CODE_CONFIG_INVALID = "gate_config_invalid"


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


def _mission_critical_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    payload = settings if isinstance(settings, dict) else {}
    raw = payload.get("mission_critical_gate")
    gate = raw if isinstance(raw, dict) else {}
    required_raw = gate.get("required_evidence_sections")
    required_sections: list[str] = []
    if isinstance(required_raw, list):
        for item in required_raw:
            section = str(item or "").strip()
            if section:
                required_sections.append(section)
    if not required_sections:
        required_sections = list(MISSION_CRITICAL_DEFAULT_REQUIRED_EVIDENCE_SECTIONS)
    approval_pattern = str(gate.get("approval_ref_pattern") or MISSION_CRITICAL_DEFAULT_APPROVAL_REF_PATTERN).strip()
    if not approval_pattern:
        approval_pattern = MISSION_CRITICAL_DEFAULT_APPROVAL_REF_PATTERN

    return {
        "enabled": bool(gate.get("enabled", False)),
        "trigger": str(gate.get("trigger") or MISSION_CRITICAL_TRIGGER_ALL_FULL_ACCESS).strip()
        or MISSION_CRITICAL_TRIGGER_ALL_FULL_ACCESS,
        "approval_ref_pattern": approval_pattern,
        "required_evidence_sections": required_sections,
    }


def _normalize_evidence_entries(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def evaluate_mission_critical_gate(
    request: dict[str, Any],
    *,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate_cfg = _mission_critical_settings(settings)
    action_scope = str(request.get("action_scope") or "workspace_only").strip() or "workspace_only"
    approval_ref = str(request.get("approval_ref") or "").strip()
    trigger = str(gate_cfg.get("trigger") or MISSION_CRITICAL_TRIGGER_ALL_FULL_ACCESS)
    enabled = bool(gate_cfg.get("enabled"))
    required_sections = [str(item) for item in gate_cfg.get("required_evidence_sections") or []]
    approval_pattern = str(gate_cfg.get("approval_ref_pattern") or MISSION_CRITICAL_DEFAULT_APPROVAL_REF_PATTERN)
    applied = enabled and trigger == MISSION_CRITICAL_TRIGGER_ALL_FULL_ACCESS and action_scope == "full_access"

    result: dict[str, Any] = {
        "applied": bool(applied),
        "passed": True,
        "code": MISSION_CRITICAL_GATE_CODE_PASSED,
        "reason": "Mission-critical gate passed",
        "trigger": trigger,
        "action_scope": action_scope,
        "approval_ref": approval_ref,
        "approval_ref_pattern": approval_pattern,
        "required_evidence_sections": required_sections,
        "missing_evidence_sections": [],
        "empty_evidence_sections": [],
    }

    if not enabled:
        result.update(
            {
                "applied": False,
                "code": MISSION_CRITICAL_GATE_CODE_DISABLED,
                "reason": "Mission-critical gate disabled",
            }
        )
        return result

    if not applied:
        result.update(
            {
                "code": MISSION_CRITICAL_GATE_CODE_NOT_APPLICABLE,
                "reason": "Mission-critical gate not applicable",
            }
        )
        return result

    if not approval_ref:
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING,
                "reason": "approval_ref is required for mission-critical full_access requests",
            }
        )
        return result

    try:
        approval_re = re.compile(approval_pattern)
    except re.error:
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_CONFIG_INVALID,
                "reason": "approval_ref_pattern is invalid in mission_critical_gate settings",
            }
        )
        return result

    if not approval_re.match(approval_ref):
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_INVALID,
                "reason": "approval_ref does not match required mission-critical format",
            }
        )
        return result

    evidence = request.get("evidence")
    if not isinstance(evidence, dict):
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_EVIDENCE_PAYLOAD_INVALID,
                "reason": "evidence payload is required and must be an object",
            }
        )
        return result

    missing_sections: list[str] = []
    empty_sections: list[str] = []
    for section in required_sections:
        if section not in evidence:
            missing_sections.append(section)
            continue
        entries = _normalize_evidence_entries(evidence.get(section))
        if not entries:
            empty_sections.append(section)

    if missing_sections:
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_MISSING,
                "reason": "missing required evidence sections",
                "missing_evidence_sections": missing_sections,
                "empty_evidence_sections": empty_sections,
            }
        )
        return result

    if empty_sections:
        result.update(
            {
                "passed": False,
                "code": MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_EMPTY,
                "reason": "required evidence sections must contain at least one entry",
                "missing_evidence_sections": missing_sections,
                "empty_evidence_sections": empty_sections,
            }
        )
        return result

    return result


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

    settings_payload: dict[str, Any] | None = None
    if isinstance(project_context, dict):
        settings_raw = project_context.get("settings")
        if isinstance(settings_raw, dict):
            settings_payload = settings_raw

    mission_gate = evaluate_mission_critical_gate(request, settings=settings_payload)
    if mission_gate.get("applied") and not mission_gate.get("passed"):
        code = str(mission_gate.get("code") or MISSION_CRITICAL_GATE_CODE_CONFIG_INVALID)
        reason = str(mission_gate.get("reason") or "mission-critical gate failed")
        return False, f"Mission-critical gate blocked dispatch: {code}: {reason}"

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
