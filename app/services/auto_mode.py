from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_PROCESSED_IDS = 5000
RUNTIME_SCHEMA_VERSION = 3
LIFECYCLE_STATUSES = {"queued", "dispatched", "reminded", "replied", "closed"}
EXTERNAL_AGENT_RE = re.compile(r"^agent-(\d+)$")


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
    actions: list[AutoModeAction]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
        lowered = env_value.lower()
        if lowered in {"repo", "dev"}:
            return root_dir / "control" / "projects"
        if lowered in {"appsupport", "app"}:
            return _default_projects_root()
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


def _normalize_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status not in LIFECYCLE_STATUSES:
        return "queued"
    return status


def _is_external_agent(agent_id: str) -> bool:
    value = str(agent_id or "").strip().lower()
    if value in {"victor", "leo"}:
        return True
    return bool(EXTERNAL_AGENT_RE.match(value))


def _normalize_runtime_request(request_id: str, payload: Any) -> dict[str, Any]:
    source: dict[str, Any] = payload if isinstance(payload, dict) else {}
    reminder_count = source.get("reminder_count", 0)
    try:
        reminder_count = int(reminder_count)
    except (TypeError, ValueError):
        reminder_count = 0

    return {
        "request_id": request_id,
        "agent_id": str(source.get("agent_id") or "").strip(),
        "status": _normalize_status(source.get("status")),
        "created_at": str(source.get("created_at") or "").strip() or None,
        "dispatched_at": str(source.get("dispatched_at") or "").strip() or None,
        "last_reminder_at": str(source.get("last_reminder_at") or "").strip() or None,
        "reminder_count": max(reminder_count, 0),
        "reply_message_id": str(source.get("reply_message_id") or "").strip() or None,
        "replied_at": str(source.get("replied_at") or "").strip() or None,
        "closed_at": str(source.get("closed_at") or "").strip() or None,
        "closed_reason": str(source.get("closed_reason") or "").strip() or None,
        "updated_at": str(source.get("updated_at") or "").strip() or None,
    }


def _legacy_closed_reason(request_payload: dict[str, Any], agent_id: str) -> str:
    source = str(request_payload.get("source") or "").strip().lower()
    if source == "reminder":
        return "reminder_event"
    if not _is_external_agent(agent_id):
        return "internal_agent_not_dispatchable"
    return "legacy_processed"


def _closed_runtime_entry(
    request_id: str,
    *,
    request_payload: dict[str, Any] | None,
    closed_reason: str,
    default_agent_id: str = "",
) -> dict[str, Any]:
    now_iso = _utc_now_iso()
    payload = request_payload or {}
    agent_id = str(payload.get("agent_id") or default_agent_id or "").strip()
    created_at = str(payload.get("created_at") or "").strip() or now_iso

    runtime_entry = _normalize_runtime_request(
        request_id,
        {
            "agent_id": agent_id,
            "status": "closed",
            "created_at": created_at,
            "closed_at": now_iso,
            "closed_reason": closed_reason,
            "updated_at": now_iso,
        },
    )
    return runtime_entry


def _build_requests_index(requests_path: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        if not request_id:
            continue
        index[request_id] = payload
    return index


def _load_state(path: Path) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, Any]]:
    if not path.exists():
        return [], {}, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], {}, {}
    if not isinstance(payload, dict):
        return [], {}, {}

    processed_raw = payload.get("processed")
    if isinstance(processed_raw, list):
        processed = [str(item).strip() for item in processed_raw if str(item).strip()]
    else:
        processed = []

    requests_raw = payload.get("requests")
    requests: dict[str, dict[str, Any]] = {}
    if isinstance(requests_raw, dict):
        for request_id, request_payload in requests_raw.items():
            rid = str(request_id).strip()
            if not rid:
                continue
            requests[rid] = _normalize_runtime_request(rid, request_payload)

    counters = payload.get("counters")
    if not isinstance(counters, dict):
        counters = {}

    return _trim_processed(processed), requests, counters


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

    normalized_counters = counters if isinstance(counters, dict) else {}
    payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": trimmed,
        "requests": normalized_requests,
        "counters": normalized_counters,
        "updated_at": _utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _recover_missing_processed_entries(
    processed: list[str],
    requests: dict[str, dict[str, Any]],
    requests_index: dict[str, dict[str, Any]],
) -> None:
    for request_id in processed:
        if request_id in requests:
            continue
        request_payload = requests_index.get(request_id)
        if request_payload:
            agent_id = str(request_payload.get("agent_id") or "").strip()
            reason = _legacy_closed_reason(request_payload, agent_id)
            requests[request_id] = _closed_runtime_entry(
                request_id,
                request_payload=request_payload,
                closed_reason=reason,
                default_agent_id=agent_id,
            )
            continue

        requests[request_id] = _closed_runtime_entry(
            request_id,
            request_payload=None,
            closed_reason="legacy_processed",
        )


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


def format_prompt(project_id: str, payload: dict[str, Any]) -> str:
    agent_id = str(payload.get("agent_id") or "").strip()
    created_at = str(payload.get("created_at") or "")
    source = str(payload.get("source") or "")
    msg = payload.get("message") or {}
    author = str((msg.get("author") if isinstance(msg, dict) else "") or "")
    text = str((msg.get("text") if isinstance(msg, dict) else "") or "")

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


def load_runtime_state(
    projects_root: Path,
    project_id: str,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    requests_path, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": _trim_processed(processed),
        "requests": requests,
        "counters": counters,
        "state_path": str(resolved_state),
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
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)

    processed_set = set(processed)

    dispatched = 0
    skipped = 0
    actions_used = 0
    actions: list[AutoModeAction] = []

    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip().lower()

        if not request_id or not agent_id:
            skipped += 1
            continue

        if request_id in processed_set:
            # Guardrail: legacy states may have processed ids with missing runtime entries.
            if request_id not in requests:
                reason = _legacy_closed_reason(payload, agent_id)
                requests[request_id] = _closed_runtime_entry(
                    request_id,
                    request_payload=payload,
                    closed_reason=reason,
                    default_agent_id=agent_id,
                )
            skipped += 1
            continue

        if source == "reminder":
            requests[request_id] = _closed_runtime_entry(
                request_id,
                request_payload=payload,
                closed_reason="reminder_event",
                default_agent_id=agent_id,
            )
            processed.append(request_id)
            processed_set.add(request_id)
            skipped += 1
            continue

        request_created_at = str(payload.get("created_at") or "").strip() or _utc_now_iso()
        now_iso = _utc_now_iso()

        requests[request_id] = _normalize_runtime_request(
            request_id,
            {
                "agent_id": agent_id,
                "status": "dispatched",
                "created_at": request_created_at,
                "dispatched_at": now_iso,
                "updated_at": now_iso,
            },
        )

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

    _save_state(resolved_state, processed, requests, counters)
    return DispatchResult(dispatched_count=dispatched, skipped_count=skipped, actions=actions)
