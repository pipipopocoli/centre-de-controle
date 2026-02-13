from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MAX_PROCESSED_IDS = 5000
MAX_REQUEST_AGE_HOURS = 24
RUNTIME_SCHEMA_VERSION = 3
MAX_TASK_TEXT_CHARS = 800
LIFECYCLE_STATUS_ORDER = {
    "queued": 0,
    "dispatched": 1,
    "reminded": 2,
    "replied": 3,
    "closed": 4,
}
OPEN_REQUEST_STATUSES = {"queued", "dispatched", "reminded"}
DEFAULT_DISPATCH_COUNTERS = {
    "ticks": 0,
    "dispatched_total": 0,
    "skipped_total": 0,
    "skipped_invalid": 0,
    "skipped_reminder": 0,
    "skipped_old": 0,
    "skipped_wrong_project": 0,
    "skipped_duplicate": 0,
    "skipped_internal_agent": 0,
    "runner_codex_success": 0,
    "runner_codex_fail": 0,
    "runner_ag_launch": 0,
    "runner_ag_pending": 0,
    "last_tick_at": None,
    "last_stats": {},
}
EXTERNAL_AGENT_RE = re.compile(r"^agent-(\d+)$")


@dataclass(frozen=True)
class AutoModeAction:
    request_id: str
    project_id: str
    agent_id: str
    platform: str
    execution_mode: str
    prompt_text: str
    app_to_open: str
    notify_text: str


@dataclass(frozen=True)
class DispatchResult:
    dispatched_count: int
    skipped_count: int
    skipped_invalid: int
    skipped_reminder: int
    skipped_old: int
    skipped_wrong_project: int
    skipped_duplicate: int
    skipped_internal_agent: int
    actions: list[AutoModeAction]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _default_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _normalize_projects_root(path: Path) -> Path:
    # Accept either the projects root or the Cockpit base dir.
    if path.name == "Cockpit":
        return path / "projects"
    if path.name != "projects" and (path / "projects").exists():
        return path / "projects"
    return path


def resolve_projects_root(data_dir: str | None, env: dict[str, str] | None = None) -> Path:
    """
    Resolve the projects root for auto-mode (projects_root/<project_id>/...).

    Priority:
    1) explicit data_dir (supports special values: repo/app)
    2) COCKPIT_DATA_DIR env
    3) App Support default
    """
    if env is None:
        env = dict(os.environ)

    root_dir = Path(__file__).resolve().parents[2]

    if data_dir:
        lowered = data_dir.lower().strip()
        if lowered in {"repo", "dev"}:
            return root_dir / "control" / "projects"
        if lowered in {"appsupport", "app"}:
            return _default_projects_root()
        return _normalize_projects_root(Path(data_dir).expanduser())

    env_value = (env.get("COCKPIT_DATA_DIR") or "").strip()
    if env_value:
        return _normalize_projects_root(Path(env_value).expanduser())

    return _default_projects_root()


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _normalize_status(raw_status: Any) -> str:
    status = str(raw_status or "").strip().lower()
    if status not in LIFECYCLE_STATUS_ORDER:
        return "queued"
    return status


def _advance_status(current_status: Any, next_status: Any) -> str:
    current = _normalize_status(current_status)
    target = _normalize_status(next_status)
    if LIFECYCLE_STATUS_ORDER[target] < LIFECYCLE_STATUS_ORDER[current]:
        return current
    return target


def _normalize_runtime_request(request_id: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    reminder_count = payload.get("reminder_count", 0)
    try:
        reminder_count = int(reminder_count)
    except (TypeError, ValueError):
        reminder_count = 0
    return {
        "request_id": request_id,
        "agent_id": str(payload.get("agent_id") or "").strip(),
        "status": _normalize_status(payload.get("status", "queued")),
        "created_at": str(payload.get("created_at") or "").strip() or None,
        "dispatched_at": str(payload.get("dispatched_at") or "").strip() or None,
        "execution_mode": str(payload.get("execution_mode") or "").strip() or None,
        "runner": str(payload.get("runner") or "").strip() or None,
        "launched_at": str(payload.get("launched_at") or "").strip() or None,
        "completed_at": str(payload.get("completed_at") or "").strip() or None,
        "completion_source": str(payload.get("completion_source") or "").strip() or None,
        "last_error": str(payload.get("last_error") or "").strip() or None,
        "last_reminder_at": str(payload.get("last_reminder_at") or "").strip() or None,
        "reminder_count": max(reminder_count, 0),
        "reply_message_id": str(payload.get("reply_message_id") or "").strip() or None,
        "replied_at": str(payload.get("replied_at") or "").strip() or None,
        "closed_at": str(payload.get("closed_at") or "").strip() or None,
        "closed_reason": str(payload.get("closed_reason") or "").strip() or None,
        "updated_at": str(payload.get("updated_at") or "").strip() or None,
    }


def _normalize_counters(payload: Any) -> dict[str, Any]:
    base = dict(DEFAULT_DISPATCH_COUNTERS)
    if not isinstance(payload, dict):
        return base
    for key in (
        "ticks",
        "dispatched_total",
        "skipped_total",
        "skipped_invalid",
        "skipped_reminder",
        "skipped_old",
        "skipped_wrong_project",
        "skipped_duplicate",
        "skipped_internal_agent",
        "runner_codex_success",
        "runner_codex_fail",
        "runner_ag_launch",
        "runner_ag_pending",
    ):
        try:
            base[key] = max(int(payload.get(key, 0)), 0)
        except (TypeError, ValueError):
            base[key] = 0
    last_tick = payload.get("last_tick_at")
    base["last_tick_at"] = str(last_tick).strip() or None if last_tick is not None else None
    last_stats = payload.get("last_stats")
    base["last_stats"] = last_stats if isinstance(last_stats, dict) else {}
    return base


def _load_state(path: Path) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, Any]]:
    try:
        if not path.exists():
            return [], {}, _normalize_counters(None)

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (PermissionError, Exception) as e:
        print(f"Warning: Failed to load auto_mode state {path}: {e}")
        return [], {}, _normalize_counters(None)

    if not isinstance(payload, dict):
        return [], {}, _normalize_counters(None)

    processed = payload.get("processed")
    if not isinstance(processed, list):
        processed_ids: list[str] = []
    else:
        processed_ids = [str(item) for item in processed if str(item).strip()]

    requests_raw = payload.get("requests")
    requests: dict[str, dict[str, Any]] = {}
    if isinstance(requests_raw, dict):
        for request_id, request_payload in requests_raw.items():
            rid = str(request_id).strip()
            if not rid:
                continue
            requests[rid] = _normalize_runtime_request(rid, request_payload)

    counters = _normalize_counters(payload.get("counters"))
    return processed_ids, requests, counters


def _trim_processed(processed: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for request_id in reversed(processed):
        rid = str(request_id).strip()
        if not rid or rid in seen:
            continue
        seen.add(rid)
        deduped.append(rid)
    deduped.reverse()
    return deduped[-MAX_PROCESSED_IDS:]


def _save_state(
    path: Path,
    processed: list[str],
    requests: dict[str, dict[str, Any]],
    counters: dict[str, Any] | None = None,
) -> None:
    trimmed = _trim_processed(processed)
    normalized_requests: dict[str, dict[str, Any]] = {}
    for request_id, payload in requests.items():
        rid = str(request_id).strip()
        if not rid:
            continue
        normalized_requests[rid] = _normalize_runtime_request(rid, payload)
    normalized_counters = _normalize_counters(counters)
    payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": trimmed,
        "requests": normalized_requests,
        "counters": normalized_counters,
        "updated_at": _utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _agent_platform(agent_id: str) -> str:
    # Locked mapping:
    # - victor, agent-1, agent-3, ... -> Codex
    # - leo, agent-2, agent-4, ... -> Antigravity
    if agent_id == "leo":
        return "antigravity"
    if agent_id == "victor":
        return "codex"
    if agent_id.startswith("agent-"):
        try:
            n = int(agent_id.split("-", 1)[1])
        except (IndexError, ValueError):
            return "codex"
        return "codex" if (n % 2 == 1) else "antigravity"
    return "codex"


def agent_platform(agent_id: str) -> str:
    return _agent_platform(agent_id)


def is_external_agent(agent_id: str) -> bool:
    value = str(agent_id or "").strip().lower()
    if value in {"victor", "leo"}:
        return True
    return bool(EXTERNAL_AGENT_RE.match(value))


def _sanitize_task_text(raw_text: str) -> str:
    text = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if "[Cockpit auto-mode]" in text:
        if "Task:\n" in text:
            text = text.split("Task:\n", 1)[-1]
        elif "Task:" in text:
            text = text.split("Task:", 1)[-1]
        if "Instructions:\n" in text:
            text = text.split("Instructions:\n", 1)[0]
        elif "Instructions:" in text:
            text = text.split("Instructions:", 1)[0]
        text = text.strip()
    if len(text) > MAX_TASK_TEXT_CHARS:
        text = text[:MAX_TASK_TEXT_CHARS].rstrip()
    return text


def format_prompt(project_id: str, payload: dict[str, Any]) -> str:
    agent_id = str(payload.get("agent_id") or "").strip()
    created_at = str(payload.get("created_at") or "")
    source = str(payload.get("source") or "")
    msg = payload.get("message") or {}
    author = str((msg.get("author") if isinstance(msg, dict) else "") or "")
    text = _sanitize_task_text(str((msg.get("text") if isinstance(msg, dict) else "") or ""))

    return (
        f"[Cockpit auto-mode]\\n"
        f"PROJECT LOCK: {project_id}\\n"
        "Do not execute for another project.\\n"
        f"Project: {project_id}\\n"
        f"Target: @{agent_id}\\n"
        f"Created: {created_at} (source={source})\\n"
        f"From: {author}\\n\\n"
        f"Task:\\n{text}\\n\\n"
        "Instructions:\\n"
        "- Do the task above.\\n"
        "- Report back in Cockpit using cockpit.post_message.\\n"
        "- Update your state with cockpit.update_agent_state (phase/percent/status).\\n"
    )


def _paths(projects_root: Path, project_id: str, state_path: Path | None) -> tuple[Path, Path, Path]:
    project_dir = projects_root / project_id
    requests_path = project_dir / "runs" / "requests.ndjson"
    inbox_dir = project_dir / "runs" / "inbox"
    resolved_state = state_path or (project_dir / "runs" / "auto_mode_state.json")
    return requests_path, inbox_dir, resolved_state


def kpi_snapshots_path(projects_root: Path, project_id: str) -> Path:
    return projects_root / project_id / "runs" / "kpi_snapshots.ndjson"


def load_runtime_state(
    projects_root: Path,
    project_id: str,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": _trim_processed(processed),
        "requests": requests,
        "counters": counters,
        "state_path": str(resolved_state),
    }


def load_dispatch_counters(
    projects_root: Path,
    project_id: str,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    runtime = load_runtime_state(projects_root, project_id, state_path=state_path)
    counters = runtime.get("counters")
    return _normalize_counters(counters)


def record_dispatch_counters(
    projects_root: Path,
    project_id: str,
    *,
    dispatched: int,
    skipped: int,
    skipped_invalid: int,
    skipped_reminder: int,
    skipped_old: int,
    skipped_wrong_project: int,
    skipped_duplicate: int,
    skipped_internal_agent: int,
    actions_used: int,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    now_iso = _utc_now_iso()

    counters["ticks"] = int(counters.get("ticks") or 0) + 1
    counters["dispatched_total"] = int(counters.get("dispatched_total") or 0) + max(int(dispatched), 0)
    counters["skipped_total"] = int(counters.get("skipped_total") or 0) + max(int(skipped), 0)
    counters["skipped_invalid"] = int(counters.get("skipped_invalid") or 0) + max(int(skipped_invalid), 0)
    counters["skipped_reminder"] = int(counters.get("skipped_reminder") or 0) + max(int(skipped_reminder), 0)
    counters["skipped_old"] = int(counters.get("skipped_old") or 0) + max(int(skipped_old), 0)
    counters["skipped_wrong_project"] = int(counters.get("skipped_wrong_project") or 0) + max(
        int(skipped_wrong_project), 0
    )
    counters["skipped_duplicate"] = int(counters.get("skipped_duplicate") or 0) + max(int(skipped_duplicate), 0)
    counters["skipped_internal_agent"] = int(counters.get("skipped_internal_agent") or 0) + max(
        int(skipped_internal_agent), 0
    )
    counters["last_tick_at"] = now_iso
    counters["last_stats"] = {
        "timestamp": now_iso,
        "dispatched": max(int(dispatched), 0),
        "skipped": max(int(skipped), 0),
        "skipped_invalid": max(int(skipped_invalid), 0),
        "skipped_reminder": max(int(skipped_reminder), 0),
        "skipped_old": max(int(skipped_old), 0),
        "skipped_wrong_project": max(int(skipped_wrong_project), 0),
        "skipped_duplicate": max(int(skipped_duplicate), 0),
        "skipped_internal_agent": max(int(skipped_internal_agent), 0),
        "actions_used": max(int(actions_used), 0),
    }

    _save_state(resolved_state, processed, requests, counters)
    return {
        "updated": True,
        "state_path": str(resolved_state),
        "counters": _normalize_counters(counters),
    }


def dispatch_once_with_counters(
    projects_root: Path,
    project_id: str,
    *,
    max_actions: int = 1,
    codex_app: str = "Codex",
    ag_app: str = "Antigravity",
    state_path: Path | None = None,
) -> DispatchResult:
    result = dispatch_once(
        projects_root,
        project_id,
        max_actions=max_actions,
        codex_app=codex_app,
        ag_app=ag_app,
        state_path=state_path,
    )
    record_dispatch_counters(
        projects_root,
        project_id,
        dispatched=result.dispatched_count,
        skipped=result.skipped_count,
        skipped_invalid=result.skipped_invalid,
        skipped_reminder=result.skipped_reminder,
        skipped_old=result.skipped_old,
        skipped_wrong_project=result.skipped_wrong_project,
        skipped_duplicate=result.skipped_duplicate,
        skipped_internal_agent=result.skipped_internal_agent,
        actions_used=len(result.actions),
        state_path=state_path,
    )
    return result


def mark_request_reminded(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    reminded_at: str | None = None,
    max_reminders: int = 3,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    rid = str(request_id).strip()
    if not rid or rid not in requests:
        return {"updated": False, "reason": "missing_request"}

    now_iso = reminded_at or _utc_now_iso()
    request = requests[rid]
    reminder_count = int(request.get("reminder_count") or 0) + 1
    request["reminder_count"] = max(reminder_count, 0)
    request["last_reminder_at"] = now_iso
    request["updated_at"] = now_iso
    if reminder_count >= max_reminders:
        request["status"] = _advance_status(request.get("status"), "closed")
        request["closed_at"] = request.get("closed_at") or now_iso
        request["closed_reason"] = "max_reminders_reached"
    else:
        request["status"] = _advance_status(request.get("status"), "reminded")
    requests[rid] = request
    _save_state(resolved_state, processed, requests, counters)
    return {
        "updated": True,
        "request_id": rid,
        "status": request.get("status"),
        "reminder_count": reminder_count,
    }


def mark_request_closed(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    closed_reason: str = "completed",
    closed_at: str | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    rid = str(request_id).strip()
    if not rid or rid not in requests:
        return {"updated": False, "reason": "missing_request"}

    now_iso = closed_at or _utc_now_iso()
    request = requests[rid]
    prev_status = _normalize_status(request.get("status"))
    next_status = _advance_status(prev_status, "closed")
    if next_status != "closed":
        return {"updated": False, "reason": "status_regression_blocked", "status": prev_status}
    request["status"] = "closed"
    request["closed_at"] = str(request.get("closed_at") or "").strip() or now_iso
    reason = str(closed_reason).strip()
    request["closed_reason"] = reason or request.get("closed_reason") or "completed"
    request["updated_at"] = now_iso
    requests[rid] = request
    _save_state(resolved_state, processed, requests, counters)
    return {
        "updated": True,
        "request_id": rid,
        "status": request.get("status"),
        "closed_reason": request.get("closed_reason"),
    }


def update_request_execution(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    agent_id: str | None = None,
    execution_mode: str | None = None,
    runner: str | None = None,
    launched: bool = False,
    completed: bool = False,
    completion_source: str | None = None,
    close_request: bool = False,
    closed_reason: str | None = None,
    error: str | None = None,
    at: str | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    rid = str(request_id).strip()
    if not rid:
        return {"updated": False, "reason": "missing_request_id"}

    request = requests.get(rid) or _normalize_runtime_request(rid, {})
    now_iso = at or _utc_now_iso()

    if agent_id is not None:
        request["agent_id"] = str(agent_id).strip()
    if execution_mode:
        request["execution_mode"] = str(execution_mode).strip()
    if runner:
        request["runner"] = str(runner).strip()
    if launched:
        request["launched_at"] = str(request.get("launched_at") or "").strip() or now_iso
    if completed:
        request["completed_at"] = now_iso
    if completion_source:
        request["completion_source"] = str(completion_source).strip()
    if error:
        request["last_error"] = str(error).strip()
    if close_request:
        request["status"] = "closed"
        request["closed_at"] = str(request.get("closed_at") or "").strip() or now_iso
        request["closed_reason"] = str(closed_reason or request.get("closed_reason") or "runner_completed").strip()

    request["updated_at"] = now_iso
    requests[rid] = _normalize_runtime_request(rid, request)

    runner_key = str(runner or "").strip().lower()
    if runner_key == "codex":
        if close_request and not error:
            counters["runner_codex_success"] = int(counters.get("runner_codex_success") or 0) + 1
        else:
            counters["runner_codex_fail"] = int(counters.get("runner_codex_fail") or 0) + 1
    elif runner_key == "antigravity" and launched:
        counters["runner_ag_launch"] = int(counters.get("runner_ag_launch") or 0) + 1

    counters["runner_ag_pending"] = sum(
        1
        for payload in requests.values()
        if isinstance(payload, dict)
        and str(payload.get("execution_mode") or "").strip() == "antigravity_supervised"
        and _normalize_status(payload.get("status")) in OPEN_REQUEST_STATUSES
    )

    _save_state(resolved_state, processed, requests, counters)
    return {
        "updated": True,
        "request_id": rid,
        "status": requests[rid].get("status"),
        "state_path": str(resolved_state),
    }


def mark_agent_replied(
    projects_root: Path,
    project_id: str,
    agent_id: str,
    *,
    reply_message_id: str | None = None,
    replied_at: str | None = None,
    state_path: Path | None = None,
) -> str | None:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    target_agent = str(agent_id).strip()
    if not target_agent:
        return None

    def _request_sort_key(request: dict[str, Any]) -> tuple[int, datetime]:
        status = _normalize_status(request.get("status"))
        rank = LIFECYCLE_STATUS_ORDER.get(status, -1)
        ts = (
            _parse_iso(str(request.get("dispatched_at") or ""))
            or _parse_iso(str(request.get("created_at") or ""))
            or _parse_iso(str(request.get("updated_at") or ""))
            or datetime.fromtimestamp(0, tz=timezone.utc)
        )
        return rank, ts

    candidates = [
        request
        for request in requests.values()
        if request.get("agent_id") == target_agent
        and _normalize_status(request.get("status")) in OPEN_REQUEST_STATUSES
    ]
    if not candidates:
        return None
    target = max(candidates, key=_request_sort_key)
    request_id = str(target.get("request_id"))
    now_iso = replied_at or _utc_now_iso()
    target["status"] = _advance_status(target.get("status"), "replied")
    target["reply_message_id"] = reply_message_id
    target["replied_at"] = now_iso
    target["updated_at"] = now_iso
    requests[request_id] = target
    _save_state(resolved_state, processed, requests, counters)
    return request_id


def iter_reminder_candidates(
    projects_root: Path,
    project_id: str,
    *,
    min_age_minutes: int = 30,
    cooldown_minutes: int = 60,
    max_reminders: int = 3,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    runtime = load_runtime_state(projects_root, project_id, state_path=state_path)
    requests = runtime.get("requests", {})
    if not isinstance(requests, dict):
        return []

    now_utc = now or datetime.now(timezone.utc)
    min_age = timedelta(minutes=max(min_age_minutes, 0))
    cooldown = timedelta(minutes=max(cooldown_minutes, 0))
    candidates: list[dict[str, Any]] = []

    for request_id, payload in requests.items():
        if not isinstance(payload, dict):
            continue
        status = _normalize_status(payload.get("status"))
        if status not in {"dispatched", "reminded"}:
            continue
        reminder_count = int(payload.get("reminder_count") or 0)
        if reminder_count >= max_reminders:
            continue

        created_at = (
            _parse_iso(str(payload.get("dispatched_at") or ""))
            or _parse_iso(str(payload.get("created_at") or ""))
        )
        if not created_at:
            continue
        if (now_utc - created_at) < min_age:
            continue

        last_reminder = _parse_iso(str(payload.get("last_reminder_at") or ""))
        if last_reminder and (now_utc - last_reminder) < cooldown:
            continue

        candidates.append(
            {
                "request_id": request_id,
                "agent_id": str(payload.get("agent_id") or "").strip(),
                "status": status,
                "created_at": payload.get("created_at"),
                "dispatched_at": payload.get("dispatched_at"),
                "reminder_count": reminder_count,
                "last_reminder_at": payload.get("last_reminder_at"),
            }
        )

    candidates.sort(
        key=lambda item: (
            _parse_iso(str(item.get("dispatched_at") or ""))
            or _parse_iso(str(item.get("created_at") or ""))
            or datetime.fromtimestamp(0, tz=timezone.utc)
        )
    )
    return candidates


def _close_stale_runtime_requests(
    requests: dict[str, dict[str, Any]],
    *,
    now_utc: datetime,
) -> None:
    cutoff = timedelta(hours=MAX_REQUEST_AGE_HOURS)
    now_iso = now_utc.replace(microsecond=0).isoformat()
    for request_id, payload in list(requests.items()):
        if not isinstance(payload, dict):
            continue
        status = _normalize_status(payload.get("status"))
        if status not in OPEN_REQUEST_STATUSES:
            continue
        created_at = (
            _parse_iso(str(payload.get("dispatched_at") or ""))
            or _parse_iso(str(payload.get("created_at") or ""))
        )
        if not created_at:
            continue
        if (now_utc - created_at) <= cutoff:
            continue
        payload["request_id"] = request_id
        payload["status"] = "closed"
        payload["closed_at"] = str(payload.get("closed_at") or "").strip() or now_iso
        payload["closed_reason"] = str(payload.get("closed_reason") or "").strip() or "stale_request"
        payload["updated_at"] = now_iso
        requests[request_id] = payload


def _filter_external(requests: dict[str, dict[str, Any]], external_only: bool) -> list[dict[str, Any]]:
    values = [item for item in requests.values() if isinstance(item, dict)]
    if not external_only:
        return values
    return [item for item in values if is_external_agent(str(item.get("agent_id") or ""))]


def _percentile_nearest_rank(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil((float(percentile) / 100.0) * len(ordered))
    index = max(min(rank - 1, len(ordered) - 1), 0)
    return ordered[index]


def compute_run_loop_kpi(
    projects_root: Path,
    project_id: str,
    *,
    now: datetime | None = None,
    window_hours: int = 24,
    external_only: bool = True,
) -> dict[str, Any]:
    runtime = load_runtime_state(projects_root, project_id)
    requests = runtime.get("requests", {})
    if not isinstance(requests, dict):
        requests = {}

    now_utc = now or datetime.now(timezone.utc)
    window = timedelta(hours=max(int(window_hours), 1))
    cutoff = now_utc - window

    request_values = _filter_external(requests, external_only)

    open_external = 0
    open_reminded = 0
    stale_queued_count = 0
    dispatched_external_24h = 0
    closed_reply_received_24h = 0
    dispatch_latency_samples: list[float] = []
    dispatch_latency_excluded_negative_24h = 0

    for payload in request_values:
        status = _normalize_status(payload.get("status"))
        created_at = _parse_iso(str(payload.get("dispatched_at") or "")) or _parse_iso(
            str(payload.get("created_at") or "")
        )
        created_at_raw = _parse_iso(str(payload.get("created_at") or ""))

        if status in OPEN_REQUEST_STATUSES:
            open_external += 1
            if status == "reminded":
                open_reminded += 1
            if created_at and (now_utc - created_at) > timedelta(hours=MAX_REQUEST_AGE_HOURS):
                stale_queued_count += 1

        dispatched_at = _parse_iso(str(payload.get("dispatched_at") or ""))
        if dispatched_at and dispatched_at >= cutoff:
            dispatched_external_24h += 1
            if created_at_raw:
                latency_seconds = (dispatched_at - created_at_raw).total_seconds()
                if latency_seconds < 0:
                    dispatch_latency_excluded_negative_24h += 1
                else:
                    dispatch_latency_samples.append(latency_seconds)

        closed_at = _parse_iso(str(payload.get("closed_at") or ""))
        closed_reason = str(payload.get("closed_reason") or "").strip().lower()
        if closed_reason == "reply_received" and closed_at and closed_at >= cutoff:
            closed_reply_received_24h += 1

    reminder_noise_pct = (open_reminded / max(open_external, 1)) * 100.0
    close_rate_24h = (closed_reply_received_24h / max(dispatched_external_24h, 1)) * 100.0
    dispatch_latency_p95 = _percentile_nearest_rank(dispatch_latency_samples, 95.0)

    return {
        "computed_at": now_utc.replace(microsecond=0).isoformat(),
        "window_hours": int(window_hours),
        "external_only": bool(external_only),
        "open_external_total": open_external,
        "open_reminded_external": open_reminded,
        "dispatched_external_24h": dispatched_external_24h,
        "closed_reply_received_24h": closed_reply_received_24h,
        "stale_queued_count": stale_queued_count,
        "reminder_noise_pct": round(reminder_noise_pct, 2),
        "close_rate_24h": round(close_rate_24h, 2),
        "dispatch_latency_p95": None if dispatch_latency_p95 is None else round(dispatch_latency_p95, 2),
        "dispatch_latency_samples_24h": len(dispatch_latency_samples),
        "dispatch_latency_excluded_negative_24h": dispatch_latency_excluded_negative_24h,
    }


def _last_snapshot_timestamp(path: Path) -> datetime | None:
    if not path.exists():
        return None
    for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        ts = _parse_iso(str(payload.get("timestamp") or ""))
        if ts:
            return ts
    return None


def emit_kpi_snapshot(
    projects_root: Path,
    project_id: str,
    *,
    snapshot_path: Path | None = None,
    post_chat: bool = True,
    min_interval_minutes: int = 25,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now or datetime.now(timezone.utc)
    path = snapshot_path or kpi_snapshots_path(projects_root, project_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    last_ts = _last_snapshot_timestamp(path)
    min_interval = timedelta(minutes=max(int(min_interval_minutes), 0))
    if last_ts and min_interval.total_seconds() > 0:
        age = now_utc - last_ts
        if age < min_interval:
            return {
                "emitted": False,
                "reason": "min_interval",
                "snapshot_path": str(path),
                "last_snapshot_at": last_ts.replace(microsecond=0).isoformat(),
                "age_seconds": int(age.total_seconds()),
            }

    kpi = compute_run_loop_kpi(projects_root, project_id, now=now_utc, window_hours=24, external_only=True)
    snapshot = {
        "timestamp": now_utc.replace(microsecond=0).isoformat(),
        "project_id": project_id,
        **kpi,
    }
    _append_ndjson(path, snapshot)

    if post_chat:
        latency_p95 = snapshot.get("dispatch_latency_p95")
        latency_samples = int(snapshot.get("dispatch_latency_samples_24h") or 0)
        if latency_p95 is None:
            dispatch_latency_text = f"- dispatch_latency_p95=n/a (n={latency_samples})"
        else:
            dispatch_latency_text = f"- dispatch_latency_p95={float(latency_p95):.2f}s (n={latency_samples})"
        text = (
            "KPI snapshot run-loop:\n"
            f"- stale_queued_count={snapshot['stale_queued_count']}\n"
            f"- reminder_noise_pct={snapshot['reminder_noise_pct']:.2f}\n"
            f"- close_rate_24h={snapshot['close_rate_24h']:.2f}\n"
            f"{dispatch_latency_text}"
        )
        chat_payload = {
            "message_id": f"msg_{now_utc.strftime('%Y%m%d_%H%M%S')}_system",
            "timestamp": snapshot["timestamp"],
            "author": "system",
            "text": text,
            "tags": ["kpi", "run-loop"],
            "mentions": [],
            "event": "kpi_snapshot",
        }
        chat_path = projects_root / project_id / "chat" / "global.ndjson"
        _append_ndjson(chat_path, chat_payload)

    return {
        "emitted": True,
        "snapshot_path": str(path),
        "snapshot": snapshot,
    }


def dispatch_once(
    projects_root: Path,
    project_id: str,
    *,
    max_actions: int = 1,
    codex_app: str = "Codex",
    ag_app: str = "Antigravity",
    state_path: Path | None = None,
) -> DispatchResult:
    """
    Read runs/requests.ndjson, write runs/inbox/<agent>.ndjson, and return up to max_actions
    prompts/app targets for the caller to execute (clipboard/open/notify).
    """
    requests_path, inbox_dir, resolved_state = _paths(projects_root, project_id, state_path)

    processed, requests, counters = _load_state(resolved_state)
    processed_set = set(processed)
    now_utc = datetime.now(timezone.utc)

    _close_stale_runtime_requests(requests, now_utc=now_utc)

    dispatched = 0
    skipped_invalid = 0
    skipped_reminder = 0
    skipped_old = 0
    skipped_wrong_project = 0
    skipped_duplicate = 0
    skipped_internal_agent = 0
    actions_used = 0
    actions: list[AutoModeAction] = []

    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip()
        created_at_raw = str(payload.get("created_at") or "").strip()
        payload_project_id = str(payload.get("project_id") or "").strip()

        if not request_id or not agent_id:
            skipped_invalid += 1
            continue
        if request_id in processed_set:
            skipped_duplicate += 1
            continue
        if payload_project_id and payload_project_id != project_id:
            wrong_state = requests.get(request_id) or _normalize_runtime_request(request_id, {})
            wrong_state["request_id"] = request_id
            wrong_state["agent_id"] = agent_id
            wrong_state["created_at"] = created_at_raw or wrong_state.get("created_at") or _utc_now_iso()
            wrong_state["status"] = "closed"
            wrong_state["closed_at"] = str(wrong_state.get("closed_at") or "").strip() or _utc_now_iso()
            wrong_state["closed_reason"] = "wrong_project"
            wrong_state["updated_at"] = _utc_now_iso()
            requests[request_id] = wrong_state
            processed.append(request_id)
            processed_set.add(request_id)
            skipped_wrong_project += 1
            continue

        if source == "reminder":
            reminder_state = requests.get(request_id) or _normalize_runtime_request(request_id, {})
            reminder_state["request_id"] = request_id
            reminder_state["agent_id"] = agent_id
            reminder_state["created_at"] = created_at_raw or reminder_state.get("created_at") or _utc_now_iso()
            reminder_state["status"] = "closed"
            reminder_state["closed_at"] = str(reminder_state.get("closed_at") or "").strip() or _utc_now_iso()
            reminder_state["closed_reason"] = str(reminder_state.get("closed_reason") or "").strip() or "reminder_event"
            reminder_state["updated_at"] = _utc_now_iso()
            requests[request_id] = reminder_state
            processed.append(request_id)
            processed_set.add(request_id)
            skipped_reminder += 1
            continue

        created_at = _parse_iso(created_at_raw)
        if created_at and (now_utc - created_at) > timedelta(hours=MAX_REQUEST_AGE_HOURS):
            existing = requests.get(request_id) or _normalize_runtime_request(request_id, {})
            existing["request_id"] = request_id
            existing["agent_id"] = agent_id
            existing["created_at"] = created_at_raw or existing.get("created_at") or _utc_now_iso()
            existing["status"] = _advance_status(existing.get("status"), "closed")
            existing["closed_at"] = str(existing.get("closed_at") or "").strip() or _utc_now_iso()
            existing["closed_reason"] = "stale_request"
            existing["updated_at"] = _utc_now_iso()
            requests[request_id] = existing
            processed.append(request_id)
            processed_set.add(request_id)
            skipped_old += 1
            continue
        if not is_external_agent(agent_id):
            internal_state = requests.get(request_id) or _normalize_runtime_request(request_id, {})
            internal_state["request_id"] = request_id
            internal_state["agent_id"] = agent_id
            internal_state["created_at"] = created_at_raw or internal_state.get("created_at") or _utc_now_iso()
            internal_state["status"] = "closed"
            internal_state["closed_at"] = str(internal_state.get("closed_at") or "").strip() or _utc_now_iso()
            internal_state["closed_reason"] = "internal_agent_not_dispatchable"
            internal_state["updated_at"] = _utc_now_iso()
            requests[request_id] = internal_state
            processed.append(request_id)
            processed_set.add(request_id)
            skipped_internal_agent += 1
            continue

        request_state = requests.get(request_id) or _normalize_runtime_request(request_id, {})
        platform = _agent_platform(agent_id)
        execution_mode = "codex_headless" if platform == "codex" else "antigravity_supervised"
        request_state["request_id"] = request_id
        request_state["agent_id"] = agent_id
        request_state["created_at"] = created_at_raw or request_state.get("created_at") or _utc_now_iso()
        request_state["dispatched_at"] = _utc_now_iso()
        request_state["execution_mode"] = execution_mode
        request_state["status"] = _advance_status(request_state.get("status"), "dispatched")
        request_state["updated_at"] = _utc_now_iso()
        requests[request_id] = request_state

        # Always write inbox (scale-friendly)
        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        if max_actions > 0 and actions_used < max_actions:
            prompt = format_prompt(project_id, payload)
            app_to_open = codex_app if platform == "codex" else ag_app
            actions.append(
                AutoModeAction(
                    request_id=request_id,
                    project_id=project_id,
                    agent_id=agent_id,
                    platform=platform,
                    execution_mode=execution_mode,
                    prompt_text=prompt,
                    app_to_open=app_to_open,
                    notify_text=f"Copied task for @{agent_id} and opened {app_to_open}",
                )
            )
            actions_used += 1

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1

    _save_state(resolved_state, processed, requests, counters)
    skipped_count = (
        skipped_invalid
        + skipped_reminder
        + skipped_old
        + skipped_wrong_project
        + skipped_duplicate
        + skipped_internal_agent
    )
    return DispatchResult(
        dispatched_count=dispatched,
        skipped_count=skipped_count,
        skipped_invalid=skipped_invalid,
        skipped_reminder=skipped_reminder,
        skipped_old=skipped_old,
        skipped_wrong_project=skipped_wrong_project,
        skipped_duplicate=skipped_duplicate,
        skipped_internal_agent=skipped_internal_agent,
        actions=actions,
    )
