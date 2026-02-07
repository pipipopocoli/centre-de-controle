from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MAX_PROCESSED_IDS = 5000
MAX_REQUEST_AGE_HOURS = 24
RUNTIME_SCHEMA_VERSION = 2
LIFECYCLE_STATUS_ORDER = {
    "queued": 0,
    "dispatched": 1,
    "reminded": 2,
    "replied": 3,
    "closed": 4,
}
OPEN_REQUEST_STATUSES = {"queued", "dispatched", "reminded"}


@dataclass(frozen=True)
class AutoModeAction:
    request_id: str
    agent_id: str
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
    skipped_duplicate: int
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
        "last_reminder_at": str(payload.get("last_reminder_at") or "").strip() or None,
        "reminder_count": max(reminder_count, 0),
        "reply_message_id": str(payload.get("reply_message_id") or "").strip() or None,
        "replied_at": str(payload.get("replied_at") or "").strip() or None,
        "closed_reason": str(payload.get("closed_reason") or "").strip() or None,
        "updated_at": str(payload.get("updated_at") or "").strip() or None,
    }


def _load_state(path: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if not path.exists():
        return [], {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], {}
    if not isinstance(payload, dict):
        return [], {}
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

    return processed_ids, requests


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


def _save_state(path: Path, processed: list[str], requests: dict[str, dict[str, Any]]) -> None:
    trimmed = _trim_processed(processed)
    normalized_requests: dict[str, dict[str, Any]] = {}
    for request_id, payload in requests.items():
        rid = str(request_id).strip()
        if not rid:
            continue
        normalized_requests[rid] = _normalize_runtime_request(rid, payload)
    payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": trimmed,
        "requests": normalized_requests,
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


def format_prompt(project_id: str, payload: dict[str, Any]) -> str:
    agent_id = str(payload.get("agent_id") or "").strip()
    created_at = str(payload.get("created_at") or "")
    source = str(payload.get("source") or "")
    msg = payload.get("message") or {}
    author = str((msg.get("author") if isinstance(msg, dict) else "") or "")
    text = str((msg.get("text") if isinstance(msg, dict) else "") or "")

    return (
        f"[Cockpit auto-mode]\\n"
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


def load_runtime_state(
    projects_root: Path,
    project_id: str,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    _, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests = _load_state(resolved_state)
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": _trim_processed(processed),
        "requests": requests,
        "state_path": str(resolved_state),
    }


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
    processed, requests = _load_state(resolved_state)
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
        request["closed_reason"] = "max_reminders_reached"
    else:
        request["status"] = _advance_status(request.get("status"), "reminded")
    requests[rid] = request
    _save_state(resolved_state, processed, requests)
    return {
        "updated": True,
        "request_id": rid,
        "status": request.get("status"),
        "reminder_count": reminder_count,
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
    processed, requests = _load_state(resolved_state)
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
    _save_state(resolved_state, processed, requests)
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

    processed, requests = _load_state(resolved_state)
    processed_set = set(processed)
    now_utc = datetime.now(timezone.utc)

    dispatched = 0
    skipped_invalid = 0
    skipped_reminder = 0
    skipped_old = 0
    skipped_duplicate = 0
    actions_used = 0
    actions: list[AutoModeAction] = []

    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip()
        created_at_raw = str(payload.get("created_at") or "").strip()

        if not request_id or not agent_id:
            skipped_invalid += 1
            continue
        if source == "reminder":
            skipped_reminder += 1
            continue
        created_at = _parse_iso(created_at_raw)
        if created_at and (now_utc - created_at) > timedelta(hours=MAX_REQUEST_AGE_HOURS):
            existing = requests.get(request_id) or _normalize_runtime_request(request_id, {})
            existing["request_id"] = request_id
            existing["agent_id"] = agent_id
            existing["created_at"] = created_at_raw or existing.get("created_at") or _utc_now_iso()
            existing["status"] = _advance_status(existing.get("status"), "closed")
            existing["closed_reason"] = "stale_request"
            existing["updated_at"] = _utc_now_iso()
            requests[request_id] = existing
            skipped_old += 1
            continue
        if request_id in processed_set:
            skipped_duplicate += 1
            continue

        request_state = requests.get(request_id) or _normalize_runtime_request(request_id, {})
        request_state["request_id"] = request_id
        request_state["agent_id"] = agent_id
        request_state["created_at"] = created_at_raw or request_state.get("created_at") or _utc_now_iso()
        request_state["dispatched_at"] = _utc_now_iso()
        request_state["status"] = _advance_status(request_state.get("status"), "dispatched")
        request_state["updated_at"] = _utc_now_iso()
        requests[request_id] = request_state

        # Always write inbox (scale-friendly)
        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        if max_actions > 0 and actions_used < max_actions:
            prompt = format_prompt(project_id, payload)
            platform = _agent_platform(agent_id)
            app_to_open = codex_app if platform == "codex" else ag_app
            actions.append(
                AutoModeAction(
                    request_id=request_id,
                    agent_id=agent_id,
                    prompt_text=prompt,
                    app_to_open=app_to_open,
                    notify_text=f"Copied task for @{agent_id} and opened {app_to_open}",
                )
            )
            actions_used += 1

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1

    _save_state(resolved_state, processed, requests)
    skipped_count = skipped_invalid + skipped_reminder + skipped_old + skipped_duplicate
    return DispatchResult(
        dispatched_count=dispatched,
        skipped_count=skipped_count,
        skipped_invalid=skipped_invalid,
        skipped_reminder=skipped_reminder,
        skipped_old=skipped_old,
        skipped_duplicate=skipped_duplicate,
        actions=actions,
    )
