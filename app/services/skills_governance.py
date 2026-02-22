from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_TRUST_TIERS = {"T0", "T1", "T2", "T3"}
TRUST_TIER_ALIASES = {
    "trusted": "T1",
    "reviewed": "T2",
    "untrusted": "T0",
}
VALID_STATUSES = {
    "proposed",
    "verified",
    "approved",
    "installed",
    "active",
    "deprecated",
    "revoked",
    "quarantined",
}
LIFECYCLE_TRANSITIONS = {
    "proposed": {"verified"},
    "verified": {"approved"},
    "approved": {"installed"},
    "installed": {"active"},
    "active": {"proposed", "deprecated", "revoked", "quarantined"},
    "deprecated": {"proposed", "revoked", "quarantined"},
    "revoked": {"quarantined"},
    "quarantined": {"revoked"},
}
ELEVATED_SCOPES = {
    "full_access",
    "outside_workspace",
    "external_fs_access",
    "elevated",
}


@dataclass(frozen=True)
class SkillLockEntry:
    skill_id: str
    repo_url: str
    commit_sha: str
    content_hash: str
    trust_tier: str
    status: str
    workspace_scope: str
    approved_by: str
    approved_at: str
    approval_ref: str
    signature: str
    provenance: dict[str, Any]


@dataclass(frozen=True)
class PolicyContext:
    project_id: str
    runner: str
    action_scope: str
    requested_skills: list[str]
    approval_ref: str | None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason_code: str
    requires_approval: bool
    runner: str
    parity_key: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_hex_like(value: str, min_len: int = 6) -> bool:
    text = str(value or "").strip().lower()
    if len(text) < min_len:
        return False
    return all(ch in "0123456789abcdef" for ch in text)


def _normalize_tier(value: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper in VALID_TRUST_TIERS:
        return upper
    alias = TRUST_TIER_ALIASES.get(raw.lower())
    if alias in VALID_TRUST_TIERS:
        return alias
    return None


def _normalize_status(value: str) -> str | None:
    status = str(value or "").strip().lower()
    if status in VALID_STATUSES:
        return status
    return None


def _normalize_scope(value: str | None) -> str:
    scope = str(value or "").strip().lower()
    return scope or "workspace_only"


def _entry_signature_seed(entry: SkillLockEntry) -> str:
    return "|".join(
        [
            entry.skill_id,
            entry.repo_url,
            entry.commit_sha,
            entry.content_hash,
            entry.trust_tier,
            entry.status,
            entry.workspace_scope,
        ]
    )


def build_entry_signature(entry: SkillLockEntry) -> str:
    return hashlib.sha256(_entry_signature_seed(entry).encode("utf-8")).hexdigest()


def _policy_parity_key(action_scope: str, requested_skills: list[str], requires_approval: bool) -> str:
    payload = {
        "action_scope": action_scope,
        "requested_skills": sorted(set(requested_skills)),
        "requires_approval": bool(requires_approval),
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _entry_from_raw(raw: dict[str, Any]) -> SkillLockEntry:
    skill_id = str(raw.get("skill_id") or raw.get("name") or "").strip()
    repo_url = str(raw.get("repo_url") or "").strip()
    commit_sha = str(raw.get("commit_sha") or raw.get("commit_pin") or "").strip()
    content_hash = str(raw.get("content_hash") or raw.get("artifact_digest") or "").strip()
    trust_tier = _normalize_tier(str(raw.get("trust_tier") or "")) or ""
    status = _normalize_status(str(raw.get("status") or "active")) or ""
    workspace_scope = _normalize_scope(str(raw.get("workspace_scope") or raw.get("scope") or "workspace_only"))
    approved_by = str(raw.get("approved_by") or "").strip()
    approved_at = str(raw.get("approved_at") or "").strip()
    approval_ref = str(raw.get("approval_ref") or "").strip()
    signature = str(raw.get("signature") or "").strip()
    provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
    return SkillLockEntry(
        skill_id=skill_id,
        repo_url=repo_url,
        commit_sha=commit_sha,
        content_hash=content_hash,
        trust_tier=trust_tier,
        status=status,
        workspace_scope=workspace_scope,
        approved_by=approved_by,
        approved_at=approved_at,
        approval_ref=approval_ref,
        signature=signature,
        provenance=provenance,
    )


def validate_entry_signature(entry: SkillLockEntry) -> bool:
    expected = build_entry_signature(entry)
    return str(entry.signature or "").strip().lower() == expected.lower()


def validate_provenance(entry: SkillLockEntry) -> bool:
    prov = entry.provenance
    if not isinstance(prov, dict):
        return False
    for key in ("source_uri", "builder", "source_digest", "build_digest", "timestamp"):
        if not str(prov.get(key) or "").strip():
            return False
    if not _is_hex_like(str(prov.get("source_digest") or ""), min_len=8):
        return False
    if not _is_hex_like(str(prov.get("build_digest") or ""), min_len=8):
        return False
    return True


def validate_tier_upgrade(
    current_tier: str,
    next_tier: str,
    *,
    approval_ref: str | None = None,
    security_reviewed: bool = False,
) -> tuple[bool, str]:
    src = _normalize_tier(current_tier)
    dst = _normalize_tier(next_tier)
    if src is None or dst is None:
        return False, "invalid_tier"
    src_level = int(src[1:])
    dst_level = int(dst[1:])
    if dst_level <= src_level:
        return True, "non_upgrade_or_equal"
    if dst_level >= 2 and not str(approval_ref or "").strip():
        return False, "approval_ref_required_for_t2_t3"
    if dst_level >= 3 and not bool(security_reviewed):
        return False, "security_review_required_for_t3"
    return True, "tier_upgrade_allowed"


def validate_lifecycle_transition(previous_status: str, new_status: str) -> bool:
    prev = _normalize_status(previous_status)
    nxt = _normalize_status(new_status)
    if prev is None or nxt is None:
        return False
    allowed = LIFECYCLE_TRANSITIONS.get(prev, set())
    return nxt in allowed


def validate_skills_lock(lock_payload: dict[str, Any]) -> tuple[bool, list[str], list[SkillLockEntry]]:
    errors: list[str] = []
    entries: list[SkillLockEntry] = []
    if not isinstance(lock_payload, dict):
        return False, ["lock_payload_not_dict"], []

    skills_raw = lock_payload.get("skills")
    if not isinstance(skills_raw, list):
        return False, ["skills_array_missing"], []

    for index, raw in enumerate(skills_raw):
        if not isinstance(raw, dict):
            errors.append(f"entry_{index}_not_object")
            continue
        entry = _entry_from_raw(raw)
        if not entry.skill_id:
            errors.append(f"entry_{index}_missing_skill_id")
        if not entry.repo_url:
            errors.append(f"entry_{index}_missing_repo_url")
        if not _is_hex_like(entry.commit_sha, min_len=7):
            errors.append(f"entry_{index}_invalid_commit_sha")
        if not _is_hex_like(entry.content_hash, min_len=8):
            errors.append(f"entry_{index}_invalid_content_hash")
        if entry.trust_tier not in VALID_TRUST_TIERS:
            errors.append(f"entry_{index}_invalid_trust_tier")
        if entry.status not in VALID_STATUSES:
            errors.append(f"entry_{index}_invalid_status")
        if not entry.workspace_scope:
            errors.append(f"entry_{index}_missing_workspace_scope")
        if not entry.signature:
            errors.append(f"entry_{index}_missing_signature")
        elif not validate_entry_signature(entry):
            errors.append(f"entry_{index}_invalid_signature")
        if not validate_provenance(entry):
            errors.append(f"entry_{index}_invalid_provenance")
        entries.append(entry)

    return len(errors) == 0, errors, entries


def requires_full_access_approval(action_scope: str | None, approval_ref: str | None) -> bool:
    scope = _normalize_scope(action_scope)
    if scope not in ELEVATED_SCOPES:
        return False
    return not bool(str(approval_ref or "").strip())


def evaluate_policy(context: PolicyContext) -> PolicyDecision:
    runner = str(context.runner or "").strip().lower()
    scope = _normalize_scope(context.action_scope)
    skills = [str(skill or "").strip() for skill in (context.requested_skills or []) if str(skill or "").strip()]
    requires = scope in ELEVATED_SCOPES
    parity_key = _policy_parity_key(scope, skills, requires)

    if runner not in {"codex", "antigravity"}:
        return PolicyDecision(
            allowed=False,
            reason_code="invalid_runner",
            requires_approval=requires,
            runner=runner or "unknown",
            parity_key=parity_key,
        )
    if requires_full_access_approval(scope, context.approval_ref):
        return PolicyDecision(
            allowed=False,
            reason_code="approval_ref_required",
            requires_approval=True,
            runner=runner,
            parity_key=parity_key,
        )
    return PolicyDecision(
        allowed=True,
        reason_code="allowed",
        requires_approval=requires,
        runner=runner,
        parity_key=parity_key,
    )


def skills_lock_path(projects_root: Path, project_id: str) -> Path:
    return Path(projects_root) / project_id / "skills" / "skills.lock.json"


def load_skills_lock(path: Path) -> dict[str, Any]:
    lock_path = Path(path)
    if not lock_path.exists():
        return {"schema_version": 1, "skills": [], "audit": []}
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "skills": [], "audit": []}
    if not isinstance(payload, dict):
        return {"schema_version": 1, "skills": [], "audit": []}
    if not isinstance(payload.get("skills"), list):
        payload["skills"] = []
    if not isinstance(payload.get("audit"), list):
        payload["audit"] = []
    return payload


def _write_skills_lock(path: Path, payload: dict[str, Any]) -> None:
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = lock_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(lock_path)


def _set_skill_status(
    lock_path: Path,
    skill_id: str,
    new_status: str,
    *,
    reason: str,
    actor: str,
    approval_ref: str | None = None,
) -> tuple[bool, str]:
    payload = load_skills_lock(lock_path)
    skills = payload.get("skills")
    if not isinstance(skills, list):
        return False, "invalid_lock_payload"

    target = None
    target_idx = -1
    for idx, raw in enumerate(skills):
        if not isinstance(raw, dict):
            continue
        sid = str(raw.get("skill_id") or raw.get("name") or "").strip()
        if sid == skill_id:
            target = dict(raw)
            target_idx = idx
            break
    if target is None:
        return False, "skill_not_found"

    current_status = _normalize_status(str(target.get("status") or "active")) or "active"
    next_status = _normalize_status(new_status)
    if next_status is None:
        return False, "invalid_target_status"
    if current_status == next_status:
        return True, "already_target_status"
    if not validate_lifecycle_transition(current_status, next_status):
        return False, f"invalid_transition:{current_status}->{next_status}"

    target["status"] = next_status
    skills[target_idx] = target
    payload["updated_at"] = _utc_now_iso()
    audit = payload.get("audit")
    if not isinstance(audit, list):
        audit = []
    audit.append(
        {
            "event_id": f"evt_{int(datetime.now(timezone.utc).timestamp())}_{skill_id}_{next_status}",
            "timestamp": _utc_now_iso(),
            "actor": str(actor or "system"),
            "skill_id": skill_id,
            "action": next_status,
            "previous_state": current_status,
            "new_state": next_status,
            "approval_ref": str(approval_ref or "").strip(),
            "reason": reason,
        }
    )
    payload["audit"] = audit
    _write_skills_lock(lock_path, payload)
    return True, "status_updated"


def revoke_skill(
    lock_path: Path,
    skill_id: str,
    *,
    reason: str = "security_incident",
    actor: str = "system",
    approval_ref: str | None = None,
) -> tuple[bool, str]:
    return _set_skill_status(
        lock_path,
        skill_id,
        "revoked",
        reason=reason,
        actor=actor,
        approval_ref=approval_ref,
    )


def quarantine_skill(
    lock_path: Path,
    skill_id: str,
    *,
    reason: str = "suspected_compromise",
    actor: str = "system",
    approval_ref: str | None = None,
) -> tuple[bool, str]:
    return _set_skill_status(
        lock_path,
        skill_id,
        "quarantined",
        reason=reason,
        actor=actor,
        approval_ref=approval_ref,
    )
