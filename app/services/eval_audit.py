from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.services.eval_policy import OverrideRequest


@dataclass(frozen=True)
class OverrideAuditEntry:
    run_id: str
    project_id: str
    actor: str
    approval_ref: str
    rationale: str
    verdict_before: str
    verdict_after: str
    policy_version: str
    created_at: str


def validate_override_request(override: OverrideRequest) -> tuple[bool, str]:
    if override.actor.strip() != "@clems":
        return False, "override actor must be @clems"
    if not override.approval_ref.strip():
        return False, "approval_ref is required"
    if not override.rationale.strip():
        return False, "rationale is required"
    if not override.run_id.strip():
        return False, "run_id is required"
    return True, "override request is valid"


def append_override_audit(project_root: Path, project_id: str, entry: OverrideAuditEntry) -> Path:
    audit_path = project_root / project_id / "runs" / "eval_override_audit.ndjson"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(entry)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return audit_path
