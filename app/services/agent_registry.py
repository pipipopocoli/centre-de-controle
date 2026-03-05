from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = {"openrouter"}


@dataclass(frozen=True)
class AgentMeta:
    agent_id: str
    name: str
    engine: str
    platform: str
    level: int
    lead_id: str | None
    role: str
    skills: list[str]


def registry_path(project_id: str, projects_root: Path) -> Path:
    return projects_root / project_id / "agents" / "registry.json"


def _normalize_engine(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"or", "openrouter", "cdx", "codex", "ag", "antigravity", "anti-gravity", "ollama", "local"}:
        return "OR"
    return "OR"


def _normalize_platform(value: Any, engine: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"openrouter", "or", "codex", "antigravity", "anti-gravity", "ollama", "local"}:
        return "openrouter"
    return "openrouter"


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _from_payload(agent_id: str, payload: dict[str, Any]) -> AgentMeta:
    resolved_id = str(payload.get("agent_id") or agent_id).strip() or agent_id
    engine = _normalize_engine(payload.get("engine") or payload.get("source"))
    platform = _normalize_platform(payload.get("platform"), engine)
    return AgentMeta(
        agent_id=resolved_id,
        name=str(payload.get("name") or resolved_id).strip() or resolved_id,
        engine=engine,
        platform=platform,
        level=max(0, _coerce_int(payload.get("level"), 2)),
        lead_id=str(payload.get("lead_id") or "").strip() or None,
        role=str(payload.get("role") or "specialist").strip() or "specialist",
        skills=_coerce_list(payload.get("skills")),
    )


def load_agent_registry(project_id: str, projects_root: Path) -> dict[str, AgentMeta]:
    path = registry_path(project_id, projects_root)
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    entries: dict[str, AgentMeta] = {}
    if isinstance(payload, dict):
        for key, item in payload.items():
            if not isinstance(item, dict):
                continue
            agent_id = str(item.get("agent_id") or key).strip() or str(key).strip()
            if not agent_id:
                continue
            entries[agent_id] = _from_payload(agent_id, item)
        return entries

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            agent_id = str(item.get("agent_id") or "").strip()
            if not agent_id:
                continue
            entries[agent_id] = _from_payload(agent_id, item)
    return entries


def resolve_agent_platform(agent_id: str, registry: dict[str, AgentMeta]) -> str:
    meta = registry.get(str(agent_id).strip())
    if not meta:
        # Wave 6: Nova is Global L1 fallback
        if str(agent_id).strip().lower() == "nova":
            return "openrouter"
        return "openrouter"
    return meta.platform


def registry_to_json(registry: dict[str, AgentMeta]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for agent_id in sorted(registry):
        item = asdict(registry[agent_id])
        out[agent_id] = item
    return out
