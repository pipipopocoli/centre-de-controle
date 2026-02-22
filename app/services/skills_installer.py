from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.data.paths import PROJECTS_DIR

STATUS_INSTALLED = "installed"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"
STATUS_DRY_RUN_INSTALL = "dry_run_install"
STATUS_DRY_RUN_SKIP = "dry_run_skip"

SCHEMA_VERSION = 1
STATE_FILENAME = "install_state.json"
LOG_FILENAME = "install_log.ndjson"


@dataclass(frozen=True)
class InstallAction:
    skill_id: str
    requested_version: str
    status: str
    reason: str
    error: str | None = None


@dataclass(frozen=True)
class InstallSummary:
    project_id: str
    dry_run: bool
    requested: int
    installed: int
    skipped: int
    failed: int
    would_install: int
    actions: list[InstallAction]
    state_path: str
    log_path: str
    started_at: str
    finished_at: str
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


InstallerFn = Callable[[str, str], Any]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_skill_ids(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in values:
        skill_id = str(raw).strip()
        if not skill_id:
            continue
        if skill_id in seen:
            continue
        seen.add(skill_id)
        normalized.append(skill_id)
    return normalized


def _catalog_versions(catalog: list[dict[str, Any]] | None) -> dict[str, str]:
    if not isinstance(catalog, list):
        return {}
    versions: dict[str, str] = {}
    for entry in catalog:
        if not isinstance(entry, dict):
            continue
        skill_id = str(entry.get("id") or "").strip()
        if not skill_id:
            continue
        version = str(entry.get("version") or "unknown").strip() or "unknown"
        versions[skill_id] = version
    return versions


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": None,
        "skills": {},
    }


def _state_paths(projects_root: Path, project_id: str) -> tuple[Path, Path]:
    base = projects_root / project_id / "skills"
    return base / STATE_FILENAME, base / LOG_FILENAME


def _load_state(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        return _default_state(), warnings
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - explicit fallback for corrupted state
        warnings.append(f"state_read_failed:{exc}")
        return _default_state(), warnings

    if not isinstance(payload, dict):
        warnings.append("state_invalid_payload")
        return _default_state(), warnings

    skills = payload.get("skills")
    if not isinstance(skills, dict):
        warnings.append("state_invalid_skills_map")
        skills = {}

    normalized: dict[str, dict[str, Any]] = {}
    for key, value in skills.items():
        skill_id = str(key).strip()
        if not skill_id or not isinstance(value, dict):
            continue
        normalized[skill_id] = {
            "version": str(value.get("version") or "unknown"),
            "installed_at": value.get("installed_at"),
            "last_status": str(value.get("last_status") or ""),
            "installer": str(value.get("installer") or ""),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": payload.get("updated_at"),
        "skills": normalized,
    }, warnings


def _write_state_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _installer_name(installer: InstallerFn | None) -> str:
    if installer is None:
        return "default_noop"
    if hasattr(installer, "__name__"):
        return str(getattr(installer, "__name__") or "callable")
    return installer.__class__.__name__


def _run_installer(installer: InstallerFn | None, skill_id: str, version: str) -> tuple[bool, str, str | None]:
    if installer is None:
        return True, "installed_default_noop", None
    try:
        result = installer(skill_id, version)
    except Exception as exc:  # noqa: BLE001 - installer failures are non-fatal per skill
        return False, "installer_exception", str(exc)

    if isinstance(result, bool):
        return result, "installed" if result else "installer_returned_false", None
    if isinstance(result, dict):
        success = bool(result.get("success"))
        reason = str(result.get("reason") or ("installed" if success else "installer_failed"))
        error = str(result.get("error") or "").strip() or None
        return success, reason, error
    if isinstance(result, (tuple, list)) and result:
        success = bool(result[0])
        reason = str(result[1]) if len(result) > 1 else ("installed" if success else "installer_failed")
        error = str(result[2]) if len(result) > 2 else None
        error = error.strip() if isinstance(error, str) else error
        return success, reason, error or None

    success = bool(result)
    return success, "installed" if success else "installer_returned_falsy", None


def sync_skills(
    project_id: str,
    desired_skills: list[str] | tuple[str, ...],
    *,
    projects_root: Path | None = None,
    catalog: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
    installer: InstallerFn | None = None,
    now_iso: str | None = None,
) -> InstallSummary:
    started_at = now_iso or _utc_now_iso()
    resolved_root = Path(projects_root) if projects_root is not None else PROJECTS_DIR
    state_path, log_path = _state_paths(resolved_root, project_id)

    state, warnings = _load_state(state_path)
    skill_map = state.get("skills", {})
    if not isinstance(skill_map, dict):
        skill_map = {}
        warnings.append("state_skills_reset_to_empty")

    normalized_skills = _normalize_skill_ids(list(desired_skills))
    versions = _catalog_versions(catalog)

    installed = 0
    skipped = 0
    failed = 0
    would_install = 0
    actions: list[InstallAction] = []
    installer_name = _installer_name(installer)

    for skill_id in normalized_skills:
        requested_version = versions.get(skill_id, "unknown")
        marker = skill_map.get(skill_id)
        marker_version = str((marker or {}).get("version") or "")
        marker_status = str((marker or {}).get("last_status") or "")
        already_installed = marker_version == requested_version and marker_status == STATUS_INSTALLED

        if already_installed:
            status = STATUS_DRY_RUN_SKIP if dry_run else STATUS_SKIPPED
            actions.append(
                InstallAction(
                    skill_id=skill_id,
                    requested_version=requested_version,
                    status=status,
                    reason="already_installed",
                    error=None,
                )
            )
            skipped += 1
            continue

        if dry_run:
            actions.append(
                InstallAction(
                    skill_id=skill_id,
                    requested_version=requested_version,
                    status=STATUS_DRY_RUN_INSTALL,
                    reason="would_install",
                    error=None,
                )
            )
            would_install += 1
            continue

        success, reason, error = _run_installer(installer, skill_id, requested_version)
        if success:
            installed += 1
            skill_map[skill_id] = {
                "version": requested_version,
                "installed_at": _utc_now_iso(),
                "last_status": STATUS_INSTALLED,
                "installer": installer_name,
            }
            actions.append(
                InstallAction(
                    skill_id=skill_id,
                    requested_version=requested_version,
                    status=STATUS_INSTALLED,
                    reason=reason,
                    error=None,
                )
            )
            continue

        failed += 1
        prev_installed_at = (marker or {}).get("installed_at")
        skill_map[skill_id] = {
            "version": requested_version,
            "installed_at": prev_installed_at,
            "last_status": STATUS_FAILED,
            "installer": installer_name,
        }
        actions.append(
            InstallAction(
                skill_id=skill_id,
                requested_version=requested_version,
                status=STATUS_FAILED,
                reason=reason,
                error=error,
            )
        )

    fatal_error: str | None = None
    finished_at = _utc_now_iso()

    if not dry_run:
        state_payload = {
            "schema_version": SCHEMA_VERSION,
            "updated_at": finished_at,
            "skills": skill_map,
        }
        try:
            _write_state_atomic(state_path, state_payload)
        except Exception as exc:  # noqa: BLE001 - fatal wrapper error
            fatal_error = f"state_write_failed:{exc}"

    log_payload = {
        "timestamp": finished_at,
        "project_id": project_id,
        "dry_run": bool(dry_run),
        "requested": len(normalized_skills),
        "installed": installed,
        "skipped": skipped,
        "failed": failed,
        "would_install": would_install,
        "actions": [asdict(item) for item in actions],
        "warnings": warnings,
    }
    if fatal_error:
        log_payload["error"] = fatal_error

    try:
        _append_log(log_path, log_payload)
    except Exception as exc:  # noqa: BLE001 - fatal wrapper error
        fatal_error = f"log_append_failed:{exc}"

    return InstallSummary(
        project_id=project_id,
        dry_run=bool(dry_run),
        requested=len(normalized_skills),
        installed=installed,
        skipped=skipped,
        failed=failed,
        would_install=would_install,
        actions=actions,
        state_path=str(state_path),
        log_path=str(log_path),
        started_at=started_at,
        finished_at=finished_at,
        warnings=warnings,
        error=fatal_error,
    )


def summary_to_dict(summary: InstallSummary) -> dict[str, Any]:
    payload = asdict(summary)
    payload["actions"] = [asdict(item) for item in summary.actions]
    return payload
