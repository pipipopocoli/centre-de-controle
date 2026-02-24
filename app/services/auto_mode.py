from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.services.agent_registry import load_agent_registry, resolve_agent_platform
from app.services.gatekeeper import evaluate_mission_critical_gate
from app.services.task_matcher import rank_candidates, score_task

MAX_PROCESSED_IDS = 5000
RUNTIME_SCHEMA_VERSION = 3
LIFECYCLE_STATUSES = {"queued", "dispatched", "reminded", "replied", "closed"}
OPEN_REQUEST_STATUSES = {"queued", "dispatched", "reminded"}
OPEN_LIKE_STATUSES = {"queued", "dispatched", "reminded", "pending", "in_progress", "running", "active"}
EXTERNAL_AGENT_RE = re.compile(r"^agent-(\d+)$")

DUPLICATE_RECOVERY_REASON = "duplicate_recovery"
QUEUE_HYGIENE_RUNTIME_RECOVERY_REASON = "queue_hygiene_runtime_recovery"
QUEUE_HYGIENE_RUNTIME_MISSING_LOG_RECOVERY_REASON = "queue_hygiene_runtime_missing_log_recovery"
QUEUE_RECOVERY_MUTATION_BLOCKER = "requests_log_changed_during_recovery"

COUNTER_QUEUE_EXACT_DUPE_REMOVED_TOTAL = "queue_exact_dupe_removed_total"
COUNTER_QUEUE_SEMANTIC_DUPE_CLOSED_TOTAL = "queue_semantic_dupe_closed_total"
COUNTER_RUNTIME_LOG_SYNC_CLOSED_TOTAL = "runtime_log_sync_closed_total"
COUNTER_RUNTIME_LOG_MISSING_CLOSED_TOTAL = "runtime_log_missing_closed_total"
COUNTER_QUEUE_RECOVERY_BLOCKER_TOTAL = "queue_recovery_blocker_total"
CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES = 25
HEALTHCHECK_KPI_SNAPSHOT_MAX_AGE_SECONDS = 2100
MISSION_CRITICAL_GATE_FAILED_REASON = "mission_critical_gate_failed"
CODEX_ONLY_OUTAGE_PAUSED_REASON = "codex_only_outage_paused"

COUNTER_MISSION_CRITICAL_GATE_BLOCKED_TOTAL = "mission_critical_gate_blocked_total"
COUNTER_MISSION_CRITICAL_GATE_BLOCKED_BY_CODE_PREFIX = "mission_critical_gate_blocked_code"


@dataclass(frozen=True)
class AutoModeAction:
    request_id: str
    agent_id: str
    prompt_text: str
    app_to_open: str
    notify_text: str
    project_id: str = ""
    platform: str = "codex"
    execution_mode: str = "codex_headless"
    action_scope: str = "workspace_only"
    requested_skills: list[str] = field(default_factory=list)
    approval_ref: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class DispatchResult:
    dispatched_count: int
    skipped_count: int
    actions: list[AutoModeAction]
    gate_blocked_count: int = 0
    gate_report_path: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _normalize_projects_root(path: Path) -> Path:
    if path.name == "Cockpit":
        return path / "projects"
    if path.name != "projects" and (path / "projects").exists():
        return path / "projects"
    return path


def resolve_projects_root(data_dir: str | None, env: dict[str, str] | None = None) -> Path:
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


def _counter_token(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value or "").strip().lower())
    token = token.strip("_")
    return token or "unknown"


def _write_ndjson_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".ndjson.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for payload in rows:
                if not isinstance(payload, dict):
                    continue
                handle.write(json.dumps(payload) + "\n")
        os.replace(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        st = path.stat()
    except OSError:
        return None
    return (int(st.st_mtime_ns), int(st.st_size))


def _source_message_id(payload: dict[str, Any]) -> str:
    message = payload.get("message")
    if isinstance(message, dict):
        message_id = str(message.get("message_id") or "").strip()
        if message_id:
            return message_id
    return str(payload.get("request_id") or "").strip()


def _count_open_requests(requests: dict[str, dict[str, Any]]) -> int:
    total = 0
    for payload in requests.values():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in OPEN_REQUEST_STATUSES:
            total += 1
    return total


def _requests_open_like_count(rows: list[dict[str, Any]]) -> int:
    total = 0
    for payload in rows:
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in OPEN_LIKE_STATUSES:
            total += 1
    return total


def _latest_requests_index_from_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for payload in rows:
        request_id = str(payload.get("request_id") or "").strip()
        if not request_id:
            continue
        index[request_id] = payload
    return index


def _recover_request_rows(
    rows: list[dict[str, Any]],
    *,
    now_iso: str,
) -> dict[str, Any]:
    total_before = len(rows)
    last_row_for_request: dict[str, int] = {}
    for idx, payload in enumerate(rows):
        request_id = str(payload.get("request_id") or "").strip()
        if request_id:
            last_row_for_request[request_id] = idx

    deduped_rows: list[dict[str, Any]] = []
    exact_dupes_removed = 0
    for idx, payload in enumerate(rows):
        request_id = str(payload.get("request_id") or "").strip()
        if request_id and last_row_for_request.get(request_id) != idx:
            exact_dupes_removed += 1
            continue
        deduped_rows.append(dict(payload))

    queued_groups: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = {}
    for idx, payload in enumerate(deduped_rows):
        status = str(payload.get("status") or "").strip().lower()
        if status != "queued":
            continue
        agent_id = str(payload.get("agent_id") or "").strip()
        if not agent_id:
            continue
        key = (_source_message_id(payload), agent_id)
        queued_groups.setdefault(key, []).append((idx, payload))

    semantic_dupes_closed = 0
    duplicate_groups_closed = 0
    for items in queued_groups.values():
        if len(items) <= 1:
            continue
        duplicate_groups_closed += 1

        def _row_sort_key(item: tuple[int, dict[str, Any]]) -> tuple[float, str, int]:
            row_idx, row_payload = item
            raw_created_at = str(row_payload.get("created_at") or "").strip()
            parsed_created_at = _parse_iso(raw_created_at)
            created_epoch = parsed_created_at.timestamp() if parsed_created_at is not None else float("-inf")
            return (created_epoch, raw_created_at, row_idx)

        keep_idx = max(items, key=_row_sort_key)[0]
        for row_idx, row_payload in items:
            if row_idx == keep_idx:
                continue
            current_status = str(row_payload.get("status") or "").strip().lower()
            if current_status != "closed":
                semantic_dupes_closed += 1
            row_payload.update(
                {
                    "status": "closed",
                    "closed_at": now_iso,
                    "closed_reason": DUPLICATE_RECOVERY_REASON,
                    "completion_source": DUPLICATE_RECOVERY_REASON,
                    "updated_at": now_iso,
                    "responded_at": now_iso,
                }
            )

    queued_after = 0
    for payload in deduped_rows:
        status = str(payload.get("status") or "").strip().lower()
        if status == "queued":
            queued_after += 1

    changed = bool(exact_dupes_removed or semantic_dupes_closed)
    return {
        "rows": deduped_rows,
        "total_before": int(total_before),
        "total_after": int(len(deduped_rows)),
        "exact_dupes_removed": int(exact_dupes_removed),
        "semantic_dupes_closed": int(semantic_dupes_closed),
        "duplicate_groups_closed": int(duplicate_groups_closed),
        "queued_after": int(queued_after),
        "changed": bool(changed),
    }


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
    if value in {"victor", "leo", "nova"}:
        return True
    return bool(EXTERNAL_AGENT_RE.match(value))


def _parse_iso(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
    return default


def _normalize_runtime_request(request_id: str, payload: Any) -> dict[str, Any]:
    source: dict[str, Any] = payload if isinstance(payload, dict) else {}
    reminder_count = source.get("reminder_count", 0)
    try:
        reminder_count = int(reminder_count)
    except (TypeError, ValueError):
        reminder_count = 0

    requested_skills_raw = source.get("requested_skills")
    if isinstance(requested_skills_raw, list):
        requested_skills = [str(item).strip() for item in requested_skills_raw if str(item).strip()]
    else:
        requested_skills = []

    return {
        "request_id": request_id,
        "project_id": str(source.get("project_id") or "").strip() or None,
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
        "execution_mode": str(source.get("execution_mode") or "").strip() or None,
        "runner": str(source.get("runner") or "").strip() or None,
        "launched": _normalize_bool(source.get("launched"), default=False),
        "completed": _normalize_bool(source.get("completed"), default=False),
        "completion_source": str(source.get("completion_source") or "").strip() or None,
        "error": str(source.get("error") or "").strip() or None,
        "action_scope": str(source.get("action_scope") or "workspace_only").strip() or "workspace_only",
        "approval_ref": str(source.get("approval_ref") or "").strip() or None,
        "requested_skills": requested_skills,
        "dispatch_score": source.get("dispatch_score"),
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

    return _normalize_runtime_request(
        request_id,
        {
            "project_id": payload.get("project_id"),
            "agent_id": agent_id,
            "status": "closed",
            "created_at": created_at,
            "closed_at": now_iso,
            "closed_reason": closed_reason,
            "completion_source": closed_reason,
            "updated_at": now_iso,
            "action_scope": payload.get("action_scope") or "workspace_only",
            "approval_ref": payload.get("approval_ref"),
            "requested_skills": payload.get("requested_skills") or [],
        },
    )


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


def _increment_counter(counters: dict[str, Any], key: str, delta: int = 1) -> None:
    current = counters.get(key, 0)
    try:
        value = int(current)
    except (TypeError, ValueError):
        value = 0
    counters[key] = value + int(delta)


def _agent_platform_fallback(agent_id: str) -> str:
    if agent_id == "leo":
        return "antigravity"
    if agent_id == "nova":
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


def _execution_mode_for_platform(platform: str) -> str:
    if platform == "antigravity":
        return "antigravity_supervised"
    if platform == "ollama":
        return "ollama_local"
    return "codex_headless"


def _load_project_settings(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "settings.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dispatch_config(settings: dict[str, Any]) -> dict[str, Any]:
    dispatch = settings.get("dispatch") if isinstance(settings.get("dispatch"), dict) else {}
    scoring = dispatch.get("scoring") if isinstance(dispatch.get("scoring"), dict) else {}
    backpressure = dispatch.get("backpressure") if isinstance(dispatch.get("backpressure"), dict) else {}
    outage = settings.get("outage_mode") if isinstance(settings.get("outage_mode"), dict) else {}
    credit_guard = settings.get("credit_guard") if isinstance(settings.get("credit_guard"), dict) else {}

    raw_platforms = outage.get("allowed_platforms")
    allowed_platforms: list[str] = []
    if isinstance(raw_platforms, list):
        for item in raw_platforms:
            token = str(item or "").strip().lower()
            if token in {"codex", "antigravity", "ollama"} and token not in allowed_platforms:
                allowed_platforms.append(token)

    codex_only_enabled = _normalize_bool(outage.get("codex_only_enabled"), default=False)
    if codex_only_enabled and not allowed_platforms:
        allowed_platforms = ["codex"]

    raw_agents = outage.get("allowed_agents")
    allowed_agents: list[str] = []
    if isinstance(raw_agents, list):
        for item in raw_agents:
            token = str(item or "").strip()
            if token and token not in allowed_agents:
                allowed_agents.append(token)

    max_actions_effective = 0
    if _normalize_bool(credit_guard.get("enabled"), default=False):
        try:
            max_actions_effective = max(0, int(credit_guard.get("max_actions_effective", 0) or 0))
        except (TypeError, ValueError):
            max_actions_effective = 0

    return {
        "scoring_enabled": _normalize_bool(scoring.get("enabled"), default=False),
        "weights": scoring.get("weights") if isinstance(scoring.get("weights"), dict) else {},
        "backpressure_enabled": _normalize_bool(backpressure.get("enabled"), default=False),
        "queue_target": max(1, int(backpressure.get("queue_target", 3) or 3)),
        "max_actions_hard_cap": max(1, int(backpressure.get("max_actions_hard_cap", 5) or 5)),
        "codex_only_enabled": codex_only_enabled,
        "allowed_platforms": allowed_platforms,
        "allowed_agents": set(allowed_agents),
        "credit_guard_enabled": _normalize_bool(credit_guard.get("enabled"), default=False),
        "max_actions_effective": max_actions_effective,
    }


def _cost_config(settings: dict[str, Any]) -> dict[str, Any]:
    cost = settings.get("cost") if isinstance(settings.get("cost"), dict) else {}
    monthly_budget = cost.get("monthly_budget_cad", 1200)
    try:
        monthly_budget_cad = float(monthly_budget)
    except (TypeError, ValueError):
        monthly_budget_cad = 1200.0
    return {
        "currency": str(cost.get("currency") or "CAD").strip() or "CAD",
        "monthly_budget_cad": max(0.0, monthly_budget_cad),
    }


def _slo_targets(settings: dict[str, Any]) -> dict[str, float]:
    slo = settings.get("slo") if isinstance(settings.get("slo"), dict) else {}
    targets = slo.get("targets") if isinstance(slo.get("targets"), dict) else {}

    def _as_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    return {
        "dispatch_p95_ms": max(0.0, _as_float(targets.get("dispatch_p95_ms"), 5000.0)),
        "dispatch_p99_ms": max(0.0, _as_float(targets.get("dispatch_p99_ms"), 12000.0)),
        "success_rate_min": max(0.0, min(1.0, _as_float(targets.get("success_rate_min"), 0.95))),
    }


def _agent_status(project_dir: Path, agent_id: str) -> str:
    state_path = project_dir / "agents" / agent_id / "state.json"
    if not state_path.exists():
        return "idle"
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "idle"
    if not isinstance(payload, dict):
        return "idle"
    return str(payload.get("status") or "idle").strip().lower() or "idle"


def _agent_meta(
    project_dir: Path,
    agent_id: str,
    registry: dict[str, Any],
) -> dict[str, Any]:
    registry_meta = registry.get(agent_id)
    if registry_meta is None:
        platform = _agent_platform_fallback(agent_id)
        engine = "AG" if platform == "antigravity" else ("OLLAMA" if platform == "ollama" else "CDX")
        return {
            "agent_id": agent_id,
            "name": agent_id,
            "platform": platform,
            "engine": engine,
            "level": 2,
            "lead_id": None,
            "role": "specialist",
            "skills": [],
            "status": _agent_status(project_dir, agent_id),
        }

    return {
        "agent_id": registry_meta.agent_id,
        "name": registry_meta.name,
        "platform": registry_meta.platform,
        "engine": registry_meta.engine,
        "level": registry_meta.level,
        "lead_id": registry_meta.lead_id,
        "role": registry_meta.role,
        "skills": list(registry_meta.skills),
        "status": _agent_status(project_dir, agent_id),
    }


def _history_for_agent(counters: dict[str, Any], agent_id: str) -> dict[str, Any]:
    total_key = f"agent_total_{agent_id}"
    success_key = f"agent_success_{agent_id}"
    try:
        total = int(counters.get(total_key, 0) or 0)
    except (TypeError, ValueError):
        total = 0
    try:
        success = int(counters.get(success_key, 0) or 0)
    except (TypeError, ValueError):
        success = 0
    success_rate = 0.5 if total <= 0 else max(0.0, min(float(success) / float(total), 1.0))
    return {
        "total": total,
        "success": success,
        "success_rate": success_rate,
    }


def _paths(projects_root: Path, project_id: str, state_path: Path | None) -> tuple[Path, Path, Path]:
    project_dir = projects_root / project_id
    requests_path = project_dir / "runs" / "requests.ndjson"
    inbox_dir = project_dir / "runs" / "inbox"
    resolved_state = state_path or (project_dir / "runs" / "auto_mode_state.json")
    return requests_path, inbox_dir, resolved_state


def _mission_critical_gate_report_path(projects_root: Path, project_id: str) -> Path:
    return projects_root / project_id / "runs" / "mission_critical_gate.ndjson"


def _append_mission_critical_gate_event(
    report_path: Path,
    *,
    project_id: str,
    request_id: str,
    agent_id: str,
    action_scope: str,
    approval_ref: str | None,
    gate_result: dict[str, Any],
) -> None:
    payload = {
        "timestamp": _utc_now_iso(),
        "project_id": project_id,
        "request_id": request_id,
        "agent_id": agent_id,
        "status": "denied",
        "action_scope": action_scope,
        "approval_ref": approval_ref,
        "closed_reason": MISSION_CRITICAL_GATE_FAILED_REASON,
        "code": str(gate_result.get("code") or ""),
        "reason": str(gate_result.get("reason") or ""),
        "trigger": str(gate_result.get("trigger") or ""),
        "required_evidence_sections": list(gate_result.get("required_evidence_sections") or []),
        "missing_evidence_sections": list(gate_result.get("missing_evidence_sections") or []),
        "empty_evidence_sections": list(gate_result.get("empty_evidence_sections") or []),
    }
    _append_ndjson(report_path, payload)


def load_runtime_state(
    projects_root: Path,
    project_id: str,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    requests_path, _, resolved_state = _paths(projects_root, project_id, state_path)
    processed, requests, counters = _load_state(resolved_state)
    tick_started_at = _utc_now_iso()
    _increment_counter(counters, "ticks", 1)
    counters["last_tick_at"] = tick_started_at
    counters["last_pulse_at"] = tick_started_at
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "processed": _trim_processed(processed),
        "requests": requests,
        "counters": counters,
        "state_path": str(resolved_state),
    }


def _recover_queue_state_with_paths(
    projects_root: Path,
    project_id: str,
    *,
    requests_path: Path,
    resolved_state: Path,
    persist: bool,
    now: datetime | None,
) -> dict[str, Any]:
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)
    now_iso = now_dt.replace(microsecond=0).isoformat()

    blockers: list[str] = []
    signature_before = _file_signature(requests_path)
    raw_rows = _read_ndjson(requests_path)
    recovered = _recover_request_rows(raw_rows, now_iso=now_iso)
    recovered_rows = recovered["rows"] if isinstance(recovered.get("rows"), list) else []

    log_write_performed = False
    log_write_blocked = False

    effective_rows = recovered_rows
    if persist and bool(recovered.get("changed")):
        signature_current = _file_signature(requests_path)
        if signature_before != signature_current:
            log_write_blocked = True
            blockers.append(QUEUE_RECOVERY_MUTATION_BLOCKER)
            effective_rows = _read_ndjson(requests_path)
        else:
            _write_ndjson_atomic(requests_path, recovered_rows)
            log_write_performed = True

    latest_requests_index = _latest_requests_index_from_rows(effective_rows)

    processed, requests, counters = _load_state(resolved_state)
    _recover_missing_processed_entries(processed, requests, latest_requests_index)
    open_before = _count_open_requests(requests)

    runtime_synced_closed = 0
    for request_id, payload in list(requests.items()):
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status not in OPEN_REQUEST_STATUSES:
            continue
        latest_log_payload = latest_requests_index.get(request_id)
        if not isinstance(latest_log_payload, dict):
            continue
        latest_log_status = str(latest_log_payload.get("status") or "").strip().lower()
        if latest_log_status != "closed":
            continue

        closed_reason = str(latest_log_payload.get("closed_reason") or "").strip() or QUEUE_HYGIENE_RUNTIME_RECOVERY_REASON
        closed_at = str(latest_log_payload.get("closed_at") or "").strip() or now_iso
        updated_payload = {
            **payload,
            "status": "closed",
            "closed_reason": closed_reason,
            "closed_at": closed_at,
            "completion_source": closed_reason,
            "updated_at": now_iso,
        }
        requests[request_id] = _normalize_runtime_request(request_id, updated_payload)
        if request_id not in processed:
            processed.append(request_id)
        runtime_synced_closed += 1

    # Runtime state can retain open requests that are no longer present in the
    # append-only requests ledger (for example after dedupe cleanup). Close
    # these ghost entries to keep runtime parity with the latest ledger view.
    runtime_missing_closed = 0
    for request_id, payload in list(requests.items()):
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status not in OPEN_REQUEST_STATUSES:
            continue
        if request_id in latest_requests_index:
            continue

        updated_payload = {
            **payload,
            "status": "closed",
            "closed_reason": QUEUE_HYGIENE_RUNTIME_MISSING_LOG_RECOVERY_REASON,
            "closed_at": now_iso,
            "completion_source": QUEUE_HYGIENE_RUNTIME_MISSING_LOG_RECOVERY_REASON,
            "updated_at": now_iso,
        }
        requests[request_id] = _normalize_runtime_request(request_id, updated_payload)
        if request_id not in processed:
            processed.append(request_id)
        runtime_missing_closed += 1

    applied_exact_dupes_removed = int(recovered.get("exact_dupes_removed") or 0) if log_write_performed else 0
    applied_semantic_dupes_closed = int(recovered.get("semantic_dupes_closed") or 0) if log_write_performed else 0
    applied_duplicate_groups_closed = int(recovered.get("duplicate_groups_closed") or 0) if log_write_performed else 0

    if persist:
        if applied_exact_dupes_removed > 0:
            _increment_counter(counters, COUNTER_QUEUE_EXACT_DUPE_REMOVED_TOTAL, applied_exact_dupes_removed)
        if applied_semantic_dupes_closed > 0:
            _increment_counter(counters, COUNTER_QUEUE_SEMANTIC_DUPE_CLOSED_TOTAL, applied_semantic_dupes_closed)
        if runtime_synced_closed > 0:
            _increment_counter(counters, COUNTER_RUNTIME_LOG_SYNC_CLOSED_TOTAL, runtime_synced_closed)
        if runtime_missing_closed > 0:
            _increment_counter(counters, COUNTER_RUNTIME_LOG_MISSING_CLOSED_TOTAL, runtime_missing_closed)
        if log_write_blocked:
            _increment_counter(counters, COUNTER_QUEUE_RECOVERY_BLOCKER_TOTAL, 1)

    state_persisted = False
    if persist and (
        applied_exact_dupes_removed > 0
        or applied_semantic_dupes_closed > 0
        or runtime_synced_closed > 0
        or runtime_missing_closed > 0
        or log_write_blocked
    ):
        _save_state(resolved_state, processed, requests, counters)
        state_persisted = True

    open_after = _count_open_requests(requests)
    requests_log_open_like = _requests_open_like_count(effective_rows)
    queued_after_effective = 0
    for payload in effective_rows:
        status = str(payload.get("status") or "").strip().lower()
        if status == "queued":
            queued_after_effective += 1

    return {
        "generated_at": now_iso,
        "project_id": project_id,
        "persist": bool(persist),
        "requests_path": str(requests_path),
        "state_path": str(resolved_state),
        "blockers": blockers,
        "log_write_performed": bool(log_write_performed),
        "log_write_blocked": bool(log_write_blocked),
        "exact_dupes_removed": applied_exact_dupes_removed,
        "semantic_dupes_closed": applied_semantic_dupes_closed,
        "duplicate_groups_closed": applied_duplicate_groups_closed,
        "runtime_synced_closed": int(runtime_synced_closed),
        "runtime_missing_closed": int(runtime_missing_closed),
        "queued_after": int(queued_after_effective),
        "requests_log_open_like": int(requests_log_open_like),
        "runtime_open_before": int(open_before),
        "runtime_open_after": int(open_after),
        "runtime_requests": requests,
        "state_persisted": bool(state_persisted),
        "stats": {
            "total_before": int(recovered.get("total_before") or 0),
            "total_after_attempted": int(recovered.get("total_after") or 0),
            "total_after_effective": int(len(effective_rows)),
            "attempted_exact_dupes_removed": int(recovered.get("exact_dupes_removed") or 0),
            "attempted_semantic_dupes_closed": int(recovered.get("semantic_dupes_closed") or 0),
            "attempted_duplicate_groups_closed": int(recovered.get("duplicate_groups_closed") or 0),
            "queued_after_attempted": int(recovered.get("queued_after") or 0),
            "queued_after_effective": int(queued_after_effective),
        },
    }


def recover_queue_state(
    projects_root: Path,
    project_id: str,
    *,
    persist: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    requests_path, _, resolved_state = _paths(projects_root, project_id, None)
    return _recover_queue_state_with_paths(
        projects_root,
        project_id,
        requests_path=requests_path,
        resolved_state=resolved_state,
        persist=persist,
        now=now,
    )


def compute_control_gate_snapshot(
    projects_root: Path,
    project_id: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    recovery = recover_queue_state(projects_root, project_id, persist=False, now=now_dt)
    requests_map = recovery.get("runtime_requests") if isinstance(recovery.get("runtime_requests"), dict) else {}
    stale_cutoff = now_dt - timedelta(hours=24)

    queued_runtime_requests = 0
    pending_stale_gt24h = 0

    for payload in requests_map.values():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status not in OPEN_REQUEST_STATUSES:
            continue
        queued_runtime_requests += 1
        created_at = _parse_iso(payload.get("created_at"))
        if created_at is not None and created_at < stale_cutoff:
            pending_stale_gt24h += 1

    stale_heartbeats_gt1h = 0
    agents_state_count = 0
    heartbeat_cutoff = now_dt - timedelta(hours=1)
    agents_dir = projects_root / project_id / "agents"
    for state_path in sorted(agents_dir.glob("*/state.json")):
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        heartbeat = _parse_iso(payload.get("heartbeat"))
        if heartbeat is None:
            continue
        agents_state_count += 1
        if heartbeat < heartbeat_cutoff:
            stale_heartbeats_gt1h += 1

    requests_log_open_like = int(recovery.get("requests_log_open_like") or 0)
    requests_log_path = projects_root / project_id / "runs" / "requests.ndjson"

    return {
        "generated_at": now_dt.replace(microsecond=0).isoformat(),
        "project_id": project_id,
        "queued_runtime_requests": int(queued_runtime_requests),
        "pending_stale_gt24h": int(pending_stale_gt24h),
        "stale_heartbeats_gt1h": int(stale_heartbeats_gt1h),
        "pending_stale_gt24h_ok": bool(pending_stale_gt24h == 0),
        "queued_runtime_requests_ok": bool(queued_runtime_requests <= 3),
        "stale_heartbeats_gt1h_ok": bool(stale_heartbeats_gt1h <= 2),
        "thresholds": {
            "pending_stale_gt24h_max": 0,
            "queued_runtime_requests_max": 3,
            "stale_heartbeats_gt1h_max": 2,
        },
        "sources": {
            "runtime_state_path": str(recovery.get("state_path") or ""),
            "runtime_requests_count": int(len(requests_map)),
            "requests_log_path": str(requests_log_path),
            "requests_log_open_like": int(requests_log_open_like),
            "agents_state_glob": str(agents_dir / "*/state.json"),
            "agents_state_count": int(agents_state_count),
            "runtime_sync_closed_count": int(recovery.get("runtime_synced_closed") or 0),
            "runtime_missing_closed_count": int(recovery.get("runtime_missing_closed") or 0),
            "duplicate_groups_closed_count": int(recovery.get("duplicate_groups_closed") or 0),
            "queue_recovery_blockers": list(recovery.get("blockers") or []),
        },
    }


def _dispatch_cap(
    requests: dict[str, dict[str, Any]],
    candidate_count: int,
    *,
    backpressure_enabled: bool,
    queue_target: int,
    max_actions_hard_cap: int,
) -> int:
    if candidate_count <= 0:
        return 0
    if not backpressure_enabled:
        return candidate_count

    inflight = 0
    for payload in requests.values():
        status = str(payload.get("status") or "").strip().lower()
        if status in {"dispatched", "reminded"}:
            inflight += 1

    available = max(queue_target - inflight, 0)
    cap = min(max_actions_hard_cap, available, candidate_count)
    return max(cap, 0)


def _provider_app(platform: str, codex_app: str, ag_app: str) -> str:
    if platform == "antigravity":
        return ag_app
    if platform == "ollama":
        return "Terminal"
    return codex_app


def _candidate_score(
    meta: dict[str, Any],
    payload: dict[str, Any],
    *,
    history: dict[str, Any],
    weights: dict[str, Any],
) -> float:
    return float(score_task(meta, payload, history=history, cost=None, weights=weights))


def dispatch_once(
    projects_root: Path,
    project_id: str,
    *,
    max_actions: int = 1,
    codex_app: str = "Codex",
    ag_app: str = "Antigravity",
    state_path: Path | None = None,
) -> DispatchResult:
    requests_path, inbox_dir, resolved_state = _paths(projects_root, project_id, state_path)
    project_dir = projects_root / project_id
    settings = _load_project_settings(project_dir)
    dispatch_cfg = _dispatch_config(settings)
    allowed_agents = dispatch_cfg["allowed_agents"]
    allowed_platforms = set(dispatch_cfg["allowed_platforms"])
    max_actions_cap = max_actions
    if dispatch_cfg["credit_guard_enabled"] and int(dispatch_cfg["max_actions_effective"]) > 0:
        max_actions_cap = min(max_actions, int(dispatch_cfg["max_actions_effective"]))

    _recover_queue_state_with_paths(
        projects_root,
        project_id,
        requests_path=requests_path,
        resolved_state=resolved_state,
        persist=True,
        now=None,
    )

    processed, requests, counters = _load_state(resolved_state)
    tick_started_at = _utc_now_iso()
    _increment_counter(counters, "ticks", 1)
    counters["last_tick_at"] = tick_started_at
    counters["last_pulse_at"] = tick_started_at
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)

    processed_set = set(processed)
    registry = load_agent_registry(project_id, projects_root)
    gate_report_path = _mission_critical_gate_report_path(projects_root, project_id)

    dispatched = 0
    skipped = 0
    actions_used = 0
    gate_blocked_count = 0
    actions: list[AutoModeAction] = []

    candidates: list[dict[str, Any]] = []
    request_rows = _read_ndjson(requests_path)
    latest_row_position: dict[str, int] = {}
    for row_idx, payload in enumerate(request_rows):
        request_id = str(payload.get("request_id") or "").strip()
        if request_id:
            latest_row_position[request_id] = row_idx

    for position, payload in enumerate(request_rows):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip().lower()
        payload_status = str(payload.get("status") or "").strip().lower()

        if not request_id or not agent_id:
            skipped += 1
            continue

        if latest_row_position.get(request_id, position) != position:
            skipped += 1
            continue

        if request_id in processed_set:
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

        if payload_status == "closed":
            closed_reason = str(payload.get("closed_reason") or "").strip() or QUEUE_HYGIENE_RUNTIME_RECOVERY_REASON
            requests[request_id] = _closed_runtime_entry(
                request_id,
                request_payload=payload,
                closed_reason=closed_reason,
                default_agent_id=agent_id,
            )
            processed.append(request_id)
            processed_set.add(request_id)
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
            _increment_counter(counters, "reminder_events_total", 1)
            continue

        gate_result = evaluate_mission_critical_gate(payload, settings=settings)
        if gate_result.get("applied") and not gate_result.get("passed"):
            now_iso = _utc_now_iso()
            gate_code = str(gate_result.get("code") or "mission_critical_gate_failed").strip() or "mission_critical_gate_failed"
            action_scope = str(payload.get("action_scope") or "workspace_only").strip() or "workspace_only"
            approval_ref = str(payload.get("approval_ref") or "").strip() or None
            request_created_at = str(payload.get("created_at") or "").strip() or now_iso

            requests[request_id] = _normalize_runtime_request(
                request_id,
                {
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "status": "closed",
                    "created_at": request_created_at,
                    "closed_at": now_iso,
                    "closed_reason": MISSION_CRITICAL_GATE_FAILED_REASON,
                    "completion_source": MISSION_CRITICAL_GATE_FAILED_REASON,
                    "updated_at": now_iso,
                    "action_scope": action_scope,
                    "approval_ref": approval_ref,
                    "requested_skills": payload.get("requested_skills") or [],
                    "error": gate_code,
                },
            )
            processed.append(request_id)
            processed_set.add(request_id)
            skipped += 1
            gate_blocked_count += 1
            _increment_counter(counters, COUNTER_MISSION_CRITICAL_GATE_BLOCKED_TOTAL, 1)
            _increment_counter(
                counters,
                f"{COUNTER_MISSION_CRITICAL_GATE_BLOCKED_BY_CODE_PREFIX}_{_counter_token(gate_code)}",
                1,
            )
            _append_mission_critical_gate_event(
                gate_report_path,
                project_id=project_id,
                request_id=request_id,
                agent_id=agent_id,
                action_scope=action_scope,
                approval_ref=approval_ref,
                gate_result=gate_result,
            )
            continue

        request_created_at = str(payload.get("created_at") or "").strip() or _utc_now_iso()
        meta = _agent_meta(project_dir, agent_id, registry)
        platform_hint = str(meta.get("platform") or resolve_agent_platform(agent_id, registry) or _agent_platform_fallback(agent_id))
        if platform_hint not in {"codex", "antigravity", "ollama"}:
            platform_hint = _agent_platform_fallback(agent_id)

        if allowed_agents and agent_id not in allowed_agents:
            requests[request_id] = _closed_runtime_entry(
                request_id,
                request_payload=payload,
                closed_reason=CODEX_ONLY_OUTAGE_PAUSED_REASON,
                default_agent_id=agent_id,
            )
            processed.append(request_id)
            processed_set.add(request_id)
            skipped += 1
            continue

        if dispatch_cfg["codex_only_enabled"]:
            platform_hint = "codex"
            meta["platform"] = "codex"
            meta["engine"] = "CDX"

        if allowed_platforms and platform_hint not in allowed_platforms:
            requests[request_id] = _closed_runtime_entry(
                request_id,
                request_payload=payload,
                closed_reason=CODEX_ONLY_OUTAGE_PAUSED_REASON,
                default_agent_id=agent_id,
            )
            processed.append(request_id)
            processed_set.add(request_id)
            skipped += 1
            continue

        base_entry = _normalize_runtime_request(
            request_id,
            {
                "project_id": project_id,
                "agent_id": agent_id,
                "status": "queued",
                "created_at": request_created_at,
                "updated_at": _utc_now_iso(),
                "action_scope": payload.get("action_scope") or "workspace_only",
                "approval_ref": payload.get("approval_ref"),
                "requested_skills": payload.get("requested_skills") or [],
            },
        )
        requests[request_id] = base_entry

        history = _history_for_agent(counters, agent_id)
        score_value = _candidate_score(meta, payload, history=history, weights=dispatch_cfg["weights"])

        candidates.append(
            {
                "request_id": request_id,
                "agent_id": agent_id,
                "request_payload": payload,
                "agent_meta": meta,
                "history": history,
                "weights": dispatch_cfg["weights"],
                "score": score_value,
                "position": position,
            }
        )

    if dispatch_cfg["scoring_enabled"]:
        ranked = rank_candidates(candidates)
    else:
        ranked = sorted(candidates, key=lambda item: int(item.get("position", 0)))

    cap = _dispatch_cap(
        requests,
        len(ranked),
        backpressure_enabled=dispatch_cfg["backpressure_enabled"],
        queue_target=dispatch_cfg["queue_target"],
        max_actions_hard_cap=dispatch_cfg["max_actions_hard_cap"],
    )

    selected_ids = {item["request_id"] for item in ranked[:cap]}

    for candidate in ranked:
        request_id = str(candidate.get("request_id") or "")
        agent_id = str(candidate.get("agent_id") or "")
        payload = candidate.get("request_payload") if isinstance(candidate.get("request_payload"), dict) else {}
        score_value = float(candidate.get("score") or 0.0)
        meta = candidate.get("agent_meta") if isinstance(candidate.get("agent_meta"), dict) else {}

        if request_id not in selected_ids:
            continue

        request_created_at = str(payload.get("created_at") or "").strip() or _utc_now_iso()
        now_iso = _utc_now_iso()

        platform = str(meta.get("platform") or resolve_agent_platform(agent_id, registry) or _agent_platform_fallback(agent_id))
        if platform not in {"codex", "antigravity", "ollama"}:
            platform = _agent_platform_fallback(agent_id)

        requests[request_id] = _normalize_runtime_request(
            request_id,
            {
                "project_id": project_id,
                "agent_id": agent_id,
                "status": "dispatched",
                "created_at": request_created_at,
                "dispatched_at": request_created_at,
                "updated_at": now_iso,
                "action_scope": payload.get("action_scope") or "workspace_only",
                "approval_ref": payload.get("approval_ref"),
                "requested_skills": payload.get("requested_skills") or [],
                "dispatch_score": score_value,
            },
        )

        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        if max_actions_cap > 0 and actions_used < max_actions_cap:
            prompt = format_prompt(project_id, payload)
            app_to_open = _provider_app(platform, codex_app, ag_app)
            action_scope = str(payload.get("action_scope") or "workspace_only").strip() or "workspace_only"
            requested_skills = payload.get("requested_skills")
            if isinstance(requested_skills, list):
                skills = [str(item).strip() for item in requested_skills if str(item).strip()]
            else:
                skills = []

            actions.append(
                AutoModeAction(
                    request_id=request_id,
                    project_id=project_id,
                    agent_id=agent_id,
                    platform=platform,
                    execution_mode=_execution_mode_for_platform(platform),
                    prompt_text=prompt,
                    app_to_open=app_to_open,
                    notify_text=f"Copied task for @{agent_id} and opened {app_to_open}",
                    action_scope=action_scope,
                    approval_ref=str(payload.get("approval_ref") or "").strip() or None,
                    requested_skills=skills,
                    score=score_value,
                )
            )
            actions_used += 1

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1
        _increment_counter(counters, "dispatch_total", 1)
        _increment_counter(counters, f"agent_total_{agent_id}", 1)

    counters["dispatch_last_count"] = dispatched
    counters["dispatch_last_at"] = _utc_now_iso()
    counters["last_pulse_at"] = str(counters.get("dispatch_last_at") or tick_started_at)
    counters["last_stats"] = {
        "timestamp": tick_started_at,
        "dispatched": dispatched,
        "skipped": skipped,
        "actions_used": actions_used,
        "gate_blocked": gate_blocked_count,
    }

    _save_state(resolved_state, processed, requests, counters)
    _write_slo_verdict(projects_root, project_id, settings=settings)
    return DispatchResult(
        dispatched_count=dispatched,
        skipped_count=skipped,
        actions=actions,
        gate_blocked_count=gate_blocked_count,
        gate_report_path=str(gate_report_path),
    )


def dispatch_once_with_counters(
    projects_root: Path,
    project_id: str,
    *,
    max_actions: int = 1,
    codex_app: str = "Codex",
    ag_app: str = "Antigravity",
    state_path: Path | None = None,
) -> DispatchResult:
    return dispatch_once(
        projects_root,
        project_id,
        max_actions=max_actions,
        codex_app=codex_app,
        ag_app=ag_app,
        state_path=state_path,
    )


def _agent_platform(
    agent_id: str,
    *,
    project_id: str | None = None,
    projects_root: Path | None = None,
) -> str:
    if project_id and projects_root is not None:
        registry = load_agent_registry(project_id, projects_root)
        if registry:
            resolved = resolve_agent_platform(agent_id, registry)
            if resolved in {"codex", "antigravity", "ollama"}:
                return resolved
    return _agent_platform_fallback(agent_id)


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


def update_request_execution(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    agent_id: str,
    execution_mode: str,
    runner: str,
    launched: bool,
    completed: bool,
    completion_source: str,
    close_request: bool,
    error: str | None = None,
    closed_reason: str | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    request_id = str(request_id).strip()
    if not request_id:
        return {}

    requests_path, _, resolved_state = _paths(projects_root, project_id, None)
    processed, requests, counters = _load_state(resolved_state)
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)

    base = requests.get(request_id)
    if not isinstance(base, dict):
        source_payload = requests_index.get(request_id)
        if isinstance(source_payload, dict):
            base = _normalize_runtime_request(
                request_id,
                {
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "created_at": source_payload.get("created_at") or _utc_now_iso(),
                    "status": source_payload.get("status") or "queued",
                    "action_scope": source_payload.get("action_scope") or "workspace_only",
                    "approval_ref": source_payload.get("approval_ref"),
                    "requested_skills": source_payload.get("requested_skills") or [],
                },
            )
        else:
            base = _normalize_runtime_request(
                request_id,
                {
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "created_at": _utc_now_iso(),
                    "status": "queued",
                },
            )

    now_iso = str(at or _utc_now_iso())
    status = "closed" if close_request else str(base.get("status") or "dispatched")
    if not close_request and completion_source in {"project_lock_rejected", "policy_denied"}:
        status = "dispatched"

    updated_payload = {
        **base,
        "project_id": project_id,
        "agent_id": agent_id,
        "status": status,
        "execution_mode": execution_mode,
        "runner": runner,
        "launched": bool(launched),
        "completed": bool(completed),
        "completion_source": completion_source,
        "error": str(error or "").strip() or None,
        "updated_at": now_iso,
    }

    if status == "dispatched" and not updated_payload.get("dispatched_at"):
        updated_payload["dispatched_at"] = now_iso

    if close_request:
        updated_payload["closed_at"] = now_iso
        updated_payload["closed_reason"] = str(closed_reason or "runner_completed").strip() or "runner_completed"

    requests[request_id] = _normalize_runtime_request(request_id, updated_payload)

    if request_id not in processed and close_request:
        processed.append(request_id)

    _increment_counter(counters, "execution_updates_total", 1)
    if runner == "codex":
        _increment_counter(counters, "runner_codex_total", 1)
        if close_request and completed:
            _increment_counter(counters, "runner_codex_success", 1)
            _increment_counter(counters, f"agent_success_{agent_id}", 1)
        else:
            _increment_counter(counters, "runner_codex_failed", 1)
    elif runner == "antigravity":
        if launched:
            _increment_counter(counters, "runner_ag_launch", 1)
            _increment_counter(counters, "runner_ag_pending", 1)
        else:
            _increment_counter(counters, "runner_ag_failed", 1)
    elif runner == "ollama":
        _increment_counter(counters, "runner_ollama_total", 1)
        if close_request and completed:
            _increment_counter(counters, "runner_ollama_success", 1)
            _increment_counter(counters, f"agent_success_{agent_id}", 1)

    _save_state(resolved_state, processed, requests, counters)
    settings = _load_project_settings(projects_root / project_id)
    _write_slo_verdict(projects_root, project_id, settings=settings)
    return requests[request_id]


def mark_agent_replied(
    projects_root: Path,
    project_id: str,
    agent_id: str,
    *,
    reply_message_id: str,
    replied_at: str | None = None,
) -> str | None:
    requests_path, _, resolved_state = _paths(projects_root, project_id, None)
    processed, requests, counters = _load_state(resolved_state)
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)

    candidates: list[tuple[datetime, str]] = []
    for request_id, payload in requests.items():
        if str(payload.get("agent_id") or "") != agent_id:
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status not in OPEN_REQUEST_STATUSES:
            continue
        stamp = _parse_iso(payload.get("dispatched_at")) or _parse_iso(payload.get("created_at")) or datetime.fromtimestamp(0, tz=timezone.utc)
        candidates.append((stamp, request_id))

    if not candidates:
        return None

    _, target_request_id = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    now_iso = str(replied_at or _utc_now_iso())
    payload = requests[target_request_id]
    payload.update(
        {
            "status": "replied",
            "reply_message_id": reply_message_id,
            "replied_at": now_iso,
            "completion_source": "reply_received",
            "updated_at": now_iso,
        }
    )
    requests[target_request_id] = _normalize_runtime_request(target_request_id, payload)

    _increment_counter(counters, "reply_received_total", 1)
    _save_state(resolved_state, processed, requests, counters)
    return target_request_id


def mark_request_closed(
    projects_root: Path,
    project_id: str,
    request_id: str,
    *,
    closed_reason: str,
    closed_at: str | None = None,
) -> dict[str, Any]:
    requests_path, _, resolved_state = _paths(projects_root, project_id, None)
    processed, requests, counters = _load_state(resolved_state)
    requests_index = _build_requests_index(requests_path)
    _recover_missing_processed_entries(processed, requests, requests_index)

    request_id = str(request_id).strip()
    if not request_id:
        return {}

    payload = requests.get(request_id)
    if not isinstance(payload, dict):
        source_payload = requests_index.get(request_id)
        if not isinstance(source_payload, dict):
            return {}
        payload = _normalize_runtime_request(request_id, source_payload)

    now_iso = str(closed_at or _utc_now_iso())
    payload.update(
        {
            "status": "closed",
            "closed_reason": closed_reason,
            "closed_at": now_iso,
            "completion_source": closed_reason,
            "updated_at": now_iso,
        }
    )

    requests[request_id] = _normalize_runtime_request(request_id, payload)
    if request_id not in processed:
        processed.append(request_id)

    _increment_counter(counters, "closed_total", 1)
    if closed_reason == "reply_received":
        _increment_counter(counters, "closed_reply_received_total", 1)

    _save_state(resolved_state, processed, requests, counters)
    settings = _load_project_settings(projects_root / project_id)
    _write_slo_verdict(projects_root, project_id, settings=settings)
    return requests[request_id]


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    p = max(0.0, min(100.0, p))
    rank = (p / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return float(ordered[low] + (ordered[high] - ordered[low]) * frac)


def compute_run_loop_kpi(
    projects_root: Path,
    project_id: str,
    *,
    now: datetime | None = None,
    external_only: bool = True,
) -> dict[str, Any]:
    runtime = load_runtime_state(projects_root, project_id)
    requests = runtime.get("requests") if isinstance(runtime.get("requests"), dict) else {}

    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)
    window_start = now_dt - timedelta(hours=24)

    dispatched_external_24h = 0
    closed_reply_received_24h = 0
    stale_queued_count = 0
    reminder_events = 0
    latencies_seconds: list[float] = []
    latency_negative_excluded = 0

    for payload in requests.values():
        if not isinstance(payload, dict):
            continue
        agent_id = str(payload.get("agent_id") or "")
        if external_only and not _is_external_agent(agent_id):
            continue

        status = str(payload.get("status") or "").strip().lower()
        created_at = _parse_iso(payload.get("created_at"))
        dispatched_at = _parse_iso(payload.get("dispatched_at"))
        closed_at = _parse_iso(payload.get("closed_at"))
        closed_reason = str(payload.get("closed_reason") or "").strip().lower()

        if dispatched_at is not None and dispatched_at >= window_start:
            dispatched_external_24h += 1

        if status in OPEN_REQUEST_STATUSES and created_at is not None and created_at < (now_dt - timedelta(hours=24)):
            stale_queued_count += 1

        if closed_reason == "reminder_event" or int(payload.get("reminder_count") or 0) > 0:
            reminder_events += 1

        if (
            status == "closed"
            and closed_reason == "reply_received"
            and closed_at is not None
            and closed_at >= window_start
        ):
            closed_reply_received_24h += 1

        if dispatched_at is not None and closed_at is not None and closed_at >= window_start:
            latency = (closed_at - dispatched_at).total_seconds()
            if latency < 0:
                latency_negative_excluded += 1
            else:
                latencies_seconds.append(latency)

    close_rate_24h = 100.0 if dispatched_external_24h == 0 else (closed_reply_received_24h / dispatched_external_24h) * 100.0
    reminder_noise_pct = 0.0 if dispatched_external_24h == 0 else (reminder_events / dispatched_external_24h) * 100.0

    p95_s = _percentile(latencies_seconds, 95.0)
    p99_s = _percentile(latencies_seconds, 99.0)

    return {
        "generated_at": now_dt.replace(microsecond=0).isoformat(),
        "dispatched_external_24h": int(dispatched_external_24h),
        "closed_reply_received_24h": int(closed_reply_received_24h),
        "close_rate_24h": round(close_rate_24h, 2),
        "success_rate_24h": round(close_rate_24h / 100.0, 4),
        "stale_queued_count": int(stale_queued_count),
        "reminder_noise_pct": round(reminder_noise_pct, 2),
        "dispatch_latency_p95": None if p95_s is None else round(p95_s, 3),
        "dispatch_latency_p99": None if p99_s is None else round(p99_s, 3),
        "dispatch_latency_samples_24h": len(latencies_seconds),
        "dispatch_latency_excluded_negative_24h": int(latency_negative_excluded),
    }


def kpi_snapshots_path(projects_root: Path, project_id: str) -> Path:
    return projects_root / project_id / "runs" / "kpi_snapshots.ndjson"


def emit_kpi_snapshot(
    projects_root: Path,
    project_id: str,
    *,
    now: datetime | None = None,
    post_chat: bool = True,
    min_interval_minutes: int = 30,
) -> dict[str, Any]:
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    snapshot_file = kpi_snapshots_path(projects_root, project_id)
    existing = _read_ndjson(snapshot_file)
    if existing:
        last = existing[-1]
        last_at = _parse_iso(last.get("generated_at"))
        if last_at is not None and (now_dt - last_at).total_seconds() < max(int(min_interval_minutes), 1) * 60:
            return {
                "emitted": False,
                "reason": "min_interval",
                "generated_at": now_dt.replace(microsecond=0).isoformat(),
                "last_generated_at": last_at.replace(microsecond=0).isoformat(),
            }

    kpi = compute_run_loop_kpi(projects_root, project_id, now=now_dt, external_only=True)
    _append_ndjson(snapshot_file, kpi)

    if post_chat:
        chat_path = projects_root / project_id / "chat" / "global.ndjson"
        text = (
            "kpi_snapshot "
            f"close_rate_24h={kpi.get('close_rate_24h')} "
            f"dispatch_latency_p95={kpi.get('dispatch_latency_p95')} "
            f"stale_queued_count={kpi.get('stale_queued_count')}"
        )
        _append_ndjson(
            chat_path,
            {
                "timestamp": now_dt.replace(microsecond=0).isoformat(),
                "author": "system",
                "event": "kpi_snapshot",
                "text": text,
                "mentions": [],
                "tags": ["kpi", "runloop"],
            },
        )

    return {
        "emitted": True,
        "generated_at": now_dt.replace(microsecond=0).isoformat(),
        "snapshot_path": str(snapshot_file),
        "snapshot": kpi,
    }


def emit_control_cadence_kpi_snapshot(
    projects_root: Path,
    project_id: str,
    *,
    now: datetime | None = None,
    min_interval_minutes: int = CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
) -> dict[str, Any]:
    interval = max(int(min_interval_minutes), 1)
    result = emit_kpi_snapshot(
        projects_root,
        project_id,
        now=now,
        post_chat=False,
        min_interval_minutes=interval,
    )
    payload = dict(result) if isinstance(result, dict) else {}
    payload.setdefault("snapshot_path", str(kpi_snapshots_path(projects_root, project_id)))
    payload["min_interval_minutes"] = interval
    return payload


def emit_recency_autopulse_guard(
    projects_root: Path,
    project_id: str,
    *,
    enabled: bool,
    stale_snapshot: bool,
    pulse_fresh: bool,
    hard_issues: list[str] | None = None,
    now: datetime | None = None,
    min_interval_minutes: int = CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
) -> dict[str, Any]:
    issues = [str(item).strip() for item in (hard_issues or []) if str(item).strip()]
    if not enabled:
        return {
            "attempted": False,
            "applied": False,
            "reason": "disabled",
            "snapshot_result": None,
            "hard_issues": issues,
        }
    if issues:
        return {
            "attempted": False,
            "applied": False,
            "reason": "hard_issues_present",
            "snapshot_result": None,
            "hard_issues": issues,
        }
    if not stale_snapshot:
        return {
            "attempted": False,
            "applied": False,
            "reason": "snapshot_not_stale",
            "snapshot_result": None,
            "hard_issues": issues,
        }
    if not pulse_fresh:
        return {
            "attempted": False,
            "applied": False,
            "reason": "pulse_not_fresh",
            "snapshot_result": None,
            "hard_issues": issues,
        }

    snapshot_result = emit_control_cadence_kpi_snapshot(
        projects_root,
        project_id,
        now=now,
        min_interval_minutes=min_interval_minutes,
    )
    emitted = bool(snapshot_result.get("emitted"))
    reason = "snapshot_emitted" if emitted else str(snapshot_result.get("reason") or "not_emitted")
    return {
        "attempted": True,
        "applied": emitted,
        "reason": reason,
        "snapshot_result": snapshot_result,
        "hard_issues": issues,
    }


def _write_slo_verdict(projects_root: Path, project_id: str, *, settings: dict[str, Any]) -> dict[str, Any]:
    targets = _slo_targets(settings)
    kpi = compute_run_loop_kpi(projects_root, project_id, external_only=True)

    p95_ms = None
    if isinstance(kpi.get("dispatch_latency_p95"), (int, float)):
        p95_ms = float(kpi["dispatch_latency_p95"]) * 1000.0

    p99_ms = None
    if isinstance(kpi.get("dispatch_latency_p99"), (int, float)):
        p99_ms = float(kpi["dispatch_latency_p99"]) * 1000.0

    success_rate = float(kpi.get("success_rate_24h") or 0.0)

    reasons: list[str] = []
    if p95_ms is None or p99_ms is None:
        reasons.append("insufficient_latency_samples")
    else:
        if p95_ms > targets["dispatch_p95_ms"]:
            reasons.append("dispatch_p95_over_target")
        if p99_ms > targets["dispatch_p99_ms"]:
            reasons.append("dispatch_p99_over_target")

    if success_rate < targets["success_rate_min"]:
        reasons.append("success_rate_below_target")

    verdict = "GO" if not reasons else "HOLD"

    payload = {
        "generated_at": _utc_now_iso(),
        "project_id": project_id,
        "verdict": verdict,
        "reasons": reasons,
        "metrics": {
            "dispatch_p95_ms": None if p95_ms is None else round(p95_ms, 2),
            "dispatch_p99_ms": None if p99_ms is None else round(p99_ms, 2),
            "success_rate": round(success_rate, 4),
        },
        "targets": targets,
    }

    out_path = projects_root / project_id / "runs" / "slo_verdict_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
