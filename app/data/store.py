from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.model import AgentState, PHASES, ProjectData
from app.data.paths import PROJECTS_DIR, project_dir


DEFAULT_ROADMAP = {
    "now": ["Bootstrap Centre de controle UI"],
    "next": ["Wire local data store"],
    "risks": ["Codex App Server protocol changes"],
}

DEFAULT_AGENT_ROSTER = [
    {
        "agent_id": "clems",
        "name": "Clems",
        "engine": "CDX",
        "platform": "codex",
        "level": 0,
        "lead_id": None,
        "role": "orchestrator",
        "skills": [],
    },
    {
        "agent_id": "victor",
        "name": "Victor",
        "engine": "CDX",
        "platform": "codex",
        "level": 1,
        "lead_id": "clems",
        "role": "backend_lead",
        "skills": [],
    },
    {
        "agent_id": "leo",
        "name": "Leo",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "ui_lead",
        "skills": [],
    },
    {
        "agent_id": "nova",
        "name": "Nova",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "creative_science_lead",
        "skills": [],
    },
]


def ensure_projects_root() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_text_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def _write_json_if_missing(path: Path, payload: dict[str, Any]) -> None:
    if not path.exists():
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _memory_template(agent_id: str) -> str:
    return (
        f"# Memory - {agent_id}\n\n"
        "## Role\n- ...\n\n"
        "## Facts / Constraints\n- ...\n\n"
        "## Decisions (refs ADR)\n- ...\n\n"
        "## Open Loops\n- ...\n\n"
        "## Now\n- ...\n\n"
        "## Next\n- ...\n\n"
        "## Blockers\n- ...\n\n"
        "## Links\n- ...\n"
    )


def ensure_project_structure(project_id: str, project_name: str | None = None) -> Path:
    ensure_projects_root()
    pdir = project_dir(project_id)
    agents_dir = pdir / "agents"
    chat_dir = pdir / "chat"
    threads_dir = chat_dir / "threads"
    agents_dir.mkdir(parents=True, exist_ok=True)
    threads_dir.mkdir(parents=True, exist_ok=True)

    if project_name is None:
        project_name = project_id.title()

    settings_path = pdir / "settings.json"
    settings_payload = {
        "project_id": project_id,
        "project_name": project_name,
        "feature_flags": {
            "deep_mining": False,
            "auto_mode": True,
        },
        "auto_mode": {
            "interval_seconds": 5,
            "max_actions": 1,
        },
        "dispatch": {
            "scoring": {
                "enabled": True,
                "weights": {
                    "skill_match": 0.45,
                    "availability": 0.20,
                    "cost": 0.15,
                    "history": 0.20,
                },
            },
            "backpressure": {
                "enabled": True,
                "queue_target": 3,
                "max_actions_hard_cap": 5,
            },
        },
        "automation": {
            "router": {
                "providers_order": ["codex", "antigravity", "ollama"],
                "ollama_enabled": False,
                "ollama_model": "llama3.2",
            },
        },
        "cost": {
            "currency": "CAD",
            "monthly_budget_cad": 1200,
        },
        "slo": {
            "targets": {
                "dispatch_p95_ms": 5000,
                "dispatch_p99_ms": 12000,
                "success_rate_min": 0.95,
            },
        },
        "github": {
            "repo": "",
        },
        "updated_at": _utc_now_iso(),
    }
    _write_json_if_missing(settings_path, settings_payload)

    roadmap_yml = pdir / "roadmap.yml"
    roadmap_md = pdir / "ROADMAP.md"
    state_md = pdir / "STATE.md"
    decisions_md = pdir / "DECISIONS.md"

    _write_text_if_missing(
        roadmap_yml,
        """now:\n  - Bootstrap Centre de controle UI\nnext:\n  - Wire local data store\nrisks:\n  - Codex App Server protocol changes\n""",
    )
    _write_text_if_missing(
        roadmap_md,
        "# Roadmap\n\n## Now\n- Bootstrap Centre de controle UI\n\n## Next\n- Wire local data store\n\n## Risks\n- Codex App Server protocol changes\n",
    )
    _write_text_if_missing(
        state_md,
        "# State\n\n- UI scaffold in progress.\n",
    )
    _write_text_if_missing(
        decisions_md,
        "# Decisions\n\n- No major decisions yet.\n",
    )

    global_chat = chat_dir / "global.ndjson"
    _write_text_if_missing(global_chat, "")

    ensure_default_roster(project_id)

    return pdir


def _default_appsupport_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _resolve_path(path: Path) -> Path:
    expanded = path.expanduser()
    try:
        return expanded.resolve()
    except OSError:
        return expanded.absolute()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_appsupport_projects_root(projects_root: Path | None = None) -> bool:
    root = _resolve_path(projects_root or PROJECTS_DIR)
    return root == _resolve_path(_default_appsupport_projects_root())


def _canonical_project_id_from_entry(entry: Path, projects_root: Path | None = None) -> str:
    root = projects_root or PROJECTS_DIR
    root_resolved = _resolve_path(root)
    entry_id = entry.name

    if _is_appsupport_projects_root(root) and entry_id == "demo" and (root / "cockpit").exists():
        return "cockpit"

    if not entry.exists() and not entry.is_symlink():
        return entry_id

    target = _resolve_path(entry)
    if not _is_within(target, root_resolved):
        return entry_id

    relative = target.relative_to(root_resolved)
    if not relative.parts:
        return entry_id
    return relative.parts[0]


def _canonical_project_id(project_id: str, projects_root: Path | None = None) -> str:
    raw_project_id = str(project_id or "").strip()
    if not raw_project_id:
        return raw_project_id

    root = projects_root or PROJECTS_DIR
    if _is_appsupport_projects_root(root) and raw_project_id == "demo" and (root / "cockpit").exists():
        return "cockpit"

    entry = root / raw_project_id
    if not entry.exists() and not entry.is_symlink():
        return raw_project_id

    canonical = _canonical_project_id_from_entry(entry, root)
    if canonical and canonical != raw_project_id and (root / canonical).exists():
        return canonical
    return raw_project_id


def _is_active_project_entry(entry: Path, projects_root: Path | None = None) -> bool:
    if not entry.is_dir():
        return False
    if entry.name == "_archive":
        return False

    root = projects_root or PROJECTS_DIR
    if _is_appsupport_projects_root(root) and entry.name == "demo":
        return False

    canonical = _canonical_project_id_from_entry(entry, root)
    if canonical and canonical != entry.name and (root / canonical).exists():
        return False
    return True


def ensure_demo_project() -> ProjectData:
    target_project_id = "cockpit" if _is_appsupport_projects_root() else "demo"
    target_project_name = "Cockpit" if target_project_id == "cockpit" else "Demo"
    ensure_project_structure(target_project_id, target_project_name)
    return load_project(target_project_id)


def list_projects() -> list[str]:
    if not PROJECTS_DIR.exists():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for entry in sorted(PROJECTS_DIR.iterdir(), key=lambda item: item.name):
        if not _is_active_project_entry(entry, PROJECTS_DIR):
            continue
        canonical = _canonical_project_id_from_entry(entry, PROJECTS_DIR) or entry.name
        if canonical in seen:
            continue
        seen.add(canonical)
        out.append(canonical)
    return sorted(out)


def resolve_startup_project_id(project_ids: list[str], preferred_project_id: str | None) -> str | None:
    """
    Resolve startup project id with deterministic fallback.
    Priority:
    1) preferred project id when present
    2) "cockpit" if available
    3) first project in provided list
    4) None when list is empty
    """
    if not project_ids:
        return None

    if preferred_project_id and preferred_project_id in project_ids:
        return preferred_project_id

    if "cockpit" in project_ids:
        return "cockpit"

    return project_ids[0]


def _parse_simple_roadmap(path: Path) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {"now": [], "next": [], "risks": []}
    if not path.exists():
        return data

    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            key = line[:-1].strip().lower()
            current = key if key in data else None
            continue
        if line.startswith("-") and current:
            item = line.lstrip("-").strip()
            if item:
                data[current].append(item)
    return data


def _parse_markdown_roadmap(path: Path) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {"now": [], "next": [], "risks": []}
    if not path.exists():
        return data

    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            if heading in {"now", "next", "risks", "risk"}:
                current = "risks" if heading == "risk" else heading
            else:
                current = None
            continue
        if line.startswith("-") and current:
            item = line.lstrip("-").strip()
            if item:
                data[current].append(item)
    return data


def _normalize_phase(phase: str | None) -> str:
    if not phase:
        return PHASES[0]
    raw = str(phase).strip().lower()
    synonyms = {
        "planning": "Plan",
        "init": "Plan",
        "initialization": "Plan",
        "implementation": "Implement",
        "build": "Implement",
        "executing": "Implement",
        "testing": "Test",
        "qa": "Test",
        "verifying": "Review",
        "verify": "Review",
        "release": "Ship",
        "complete": "Ship",
        "completed": "Ship",
        "done": "Ship",
    }
    if raw in synonyms:
        return synonyms[raw]
    for option in PHASES:
        if option.lower() == raw:
            return option
    return PHASES[0]


def _normalize_engine(engine: Any) -> str:
    if not engine:
        return "CDX"
    value = str(engine).strip().lower()
    if value in {"ag", "antigravity", "anti-gravity"}:
        return "AG"
    if value in {"cdx", "codex"}:
        return "CDX"
    if value in {"ollama", "local"}:
        return "OLLAMA"
    # Canonical engines for the grid are CDX/AG; default unknown to AG.
    return "AG"


def _normalize_platform(platform: Any, engine: str) -> str:
    value = str(platform or "").strip().lower()
    if value in {"codex", "antigravity", "ollama"}:
        return value
    if engine == "AG":
        return "antigravity"
    if engine == "OLLAMA":
        return "ollama"
    return "codex"


def _normalize_level(value: Any, default: int = 2) -> int:
    try:
        level = int(value)
    except (TypeError, ValueError):
        level = default
    return max(0, level)


def _normalize_role(value: Any, default: str = "specialist") -> str:
    role = str(value or "").strip()
    return role if role else default


def _normalize_skills(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        raw = value.strip()
        return [raw] if raw else []
    return []


def _default_level_lead(agent_id: str) -> tuple[int, str | None]:
    value = str(agent_id or "").strip().lower()
    if value == "clems":
        return 0, None
    if value in {"victor", "leo", "nova"}:
        return 1, "clems"
    if value.startswith("agent-"):
        try:
            index = int(value.split("-", 1)[1])
        except (IndexError, ValueError):
            return 2, "victor"
        return 2, ("victor" if (index % 2 == 1) else "leo")
    return 2, "victor"


def _default_role(agent_id: str) -> str:
    value = str(agent_id or "").strip().lower()
    if value == "clems":
        return "orchestrator"
    if value == "victor":
        return "backend_lead"
    if value == "leo":
        return "ui_lead"
    if value == "nova":
        return "creative_science_lead"
    return "specialist"


def _normalize_percent(progress: Any) -> int:
    try:
        value = int(progress)
    except (TypeError, ValueError):
        return 0
    return max(0, min(value, 100))


def _normalize_eta(eta: Any) -> int | None:
    if eta is None:
        return None
    try:
        value = int(eta)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _normalize_blockers(blockers: Any) -> list[str]:
    if not blockers:
        return []
    if isinstance(blockers, str):
        value = blockers.strip()
        return [value] if value else []
    if isinstance(blockers, list):
        return [str(item).strip() for item in blockers if str(item).strip()]
    return []


def _registry_path(project_id: str) -> Path:
    return project_dir(project_id) / "agents" / "registry.json"


def _load_registry(project_id: str) -> dict[str, dict[str, Any]]:
    path = _registry_path(project_id)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, item in payload.items():
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("agent_id") or key).strip() or str(key).strip()
        if not agent_id:
            continue
        out[agent_id] = item
    return out


def _write_registry(project_id: str, payload: dict[str, dict[str, Any]]) -> None:
    path = _registry_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _default_registry_payload() -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for item in DEFAULT_AGENT_ROSTER:
        payload[item["agent_id"]] = {
            "agent_id": item["agent_id"],
            "name": item["name"],
            "engine": item["engine"],
            "platform": item["platform"],
            "level": item["level"],
            "lead_id": item["lead_id"],
            "role": item["role"],
            "skills": list(item.get("skills") or []),
        }
    return payload


def _registry_missing_defaults(registry: dict[str, dict[str, Any]]) -> bool:
    if not isinstance(registry, dict):
        return True
    required_ids = [str(item.get("agent_id") or "").strip() for item in DEFAULT_AGENT_ROSTER]
    for agent_id in required_ids:
        if not agent_id:
            continue
        if agent_id not in registry:
            return True
    return False


def _default_state_files_missing(project_id: str) -> bool:
    agents_dir = project_dir(project_id) / "agents"
    required_ids = [str(item.get("agent_id") or "").strip() for item in DEFAULT_AGENT_ROSTER]
    for agent_id in required_ids:
        if not agent_id:
            continue
        if not (agents_dir / agent_id / "state.json").exists():
            return True
    return False


def ensure_agent_files(
    project_id: str,
    agent_id: str,
    name: str,
    engine: str,
    *,
    level: int = 2,
    lead_id: str | None = None,
    role: str = "specialist",
    platform: str | None = None,
    skills: list[str] | None = None,
) -> None:
    agent_dir = project_dir(project_id) / "agents" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)

    default_level, default_lead = _default_level_lead(agent_id)
    normalized_engine = _normalize_engine(engine)
    normalized_platform = _normalize_platform(platform, normalized_engine)
    normalized_level = _normalize_level(level, default=default_level)
    normalized_role = _normalize_role(role, default=_default_role(agent_id))
    resolved_lead_id = lead_id if lead_id is not None else default_lead
    normalized_skills = _normalize_skills(skills or [])

    state_path = agent_dir / "state.json"
    _write_json_if_missing(
        state_path,
        {
            "agent_id": agent_id,
            "name": name,
            "engine": normalized_engine,
            "platform": normalized_platform,
            "level": normalized_level,
            "lead_id": resolved_lead_id,
            "role": normalized_role,
            "skills": normalized_skills,
            "phase": PHASES[0],
            "percent": 0,
            "eta_minutes": None,
            "heartbeat": _utc_now_iso(),
            "status": "idle",
            "blockers": [],
            "current_task": "",
        },
    )
    _write_text_if_missing(agent_dir / "journal.ndjson", "")
    _write_text_if_missing(agent_dir / "memory.md", _memory_template(agent_id))


def ensure_default_roster(project_id: str) -> None:
    agents_dir = project_dir(project_id) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry = _load_registry(project_id)
    defaults = _default_registry_payload()
    registry_changed = False
    if not registry:
        registry = defaults
        registry_changed = True
    else:
        for agent_id, default_entry in defaults.items():
            current = registry.get(agent_id)
            if not isinstance(current, dict):
                registry[agent_id] = dict(default_entry)
                registry_changed = True
                continue
            merged = dict(default_entry)
            merged.update(current)
            merged["agent_id"] = agent_id
            if merged != current:
                registry[agent_id] = merged
                registry_changed = True
    if registry_changed:
        _write_registry(project_id, registry)

    for agent in DEFAULT_AGENT_ROSTER:
        ensure_agent_files(
            project_id=project_id,
            agent_id=agent["agent_id"],
            name=agent["name"],
            engine=agent["engine"],
            level=int(agent.get("level", 2)),
            lead_id=agent.get("lead_id"),
            role=str(agent.get("role") or "specialist"),
            platform=agent.get("platform"),
            skills=list(agent.get("skills") or []),
        )

    for agent_id, item in registry.items():
        ensure_agent_files(
            project_id=project_id,
            agent_id=agent_id,
            name=str(item.get("name") or agent_id),
            engine=str(item.get("engine") or "CDX"),
            level=_normalize_level(item.get("level"), default=2),
            lead_id=str(item.get("lead_id") or "").strip() or None,
            role=_normalize_role(item.get("role"), default="specialist"),
            platform=item.get("platform"),
            skills=_normalize_skills(item.get("skills")),
        )


def load_project(project_id: str) -> ProjectData:
    canonical_project_id = _canonical_project_id(project_id)
    pdir = project_dir(canonical_project_id)
    agents_dir = pdir / "agents"
    registry = _load_registry(canonical_project_id) if pdir.exists() else {}
    has_state_files = False
    if agents_dir.exists():
        has_state_files = any((candidate / "state.json").exists() for candidate in agents_dir.iterdir() if candidate.is_dir())
    if pdir.exists() and (
        not has_state_files
        or _registry_missing_defaults(registry)
        or _default_state_files_missing(canonical_project_id)
    ):
        ensure_default_roster(canonical_project_id)
        registry = _load_registry(canonical_project_id)
    settings_path = pdir / "settings.json"
    settings: dict[str, Any] = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    project_name = settings.get("project_name", canonical_project_id.title())

    agents: list[AgentState] = []
    if agents_dir.exists():
        for agent_folder in sorted([p for p in agents_dir.iterdir() if p.is_dir()]):
            state_path = agent_folder / "state.json"
            if not state_path.exists():
                continue
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            registry_entry = registry.get(agent_folder.name) if isinstance(registry, dict) else None
            if not isinstance(registry_entry, dict):
                registry_entry = {}
            settings_tasks = settings.get("agent_tasks") if isinstance(settings, dict) else {}
            task_entry = settings_tasks.get(agent_folder.name) if isinstance(settings_tasks, dict) else None
            current_task = None
            if isinstance(task_entry, dict):
                current_task = task_entry.get("current_task")
            if current_task is None:
                current_task = payload.get("current_task")

            engine = _normalize_engine(
                payload.get("engine")
                or payload.get("source")
                or registry_entry.get("engine")
            )
            platform = _normalize_platform(
                payload.get("platform") or registry_entry.get("platform"),
                engine,
            )

            agents.append(
                AgentState(
                    agent_id=payload.get("agent_id", agent_folder.name),
                    name=payload.get("name", registry_entry.get("name", agent_folder.name.title())),
                    engine=engine,
                    phase=_normalize_phase(payload.get("phase")),
                    percent=_normalize_percent(payload.get("percent", payload.get("progress", 0))),
                    eta_minutes=_normalize_eta(payload.get("eta_minutes")),
                    heartbeat=payload.get("heartbeat"),
                    status=payload.get("status"),
                    blockers=_normalize_blockers(payload.get("blockers")),
                    current_task=str(current_task).strip() if current_task else None,
                    level=_normalize_level(payload.get("level", registry_entry.get("level", 2)), default=2),
                    lead_id=str(payload.get("lead_id", registry_entry.get("lead_id")) or "").strip() or None,
                    role=_normalize_role(payload.get("role", registry_entry.get("role")), default="specialist"),
                    platform=platform,
                    skills=_normalize_skills(payload.get("skills", registry_entry.get("skills"))),
                )
            )

    roadmap_md = _parse_markdown_roadmap(pdir / "ROADMAP.md")
    if any(roadmap_md.values()):
        roadmap = roadmap_md
    else:
        roadmap = _parse_simple_roadmap(pdir / "roadmap.yml")

    return ProjectData(
        project_id=canonical_project_id,
        name=project_name,
        path=pdir,
        agents=agents,
        roadmap=roadmap,
        settings=settings,
    )


def _read_ndjson(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if limit > 0:
        lines = lines[-limit:]
    messages: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            messages.append(payload)
    return messages


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def chat_global_path(project_id: str) -> Path:
    return project_dir(project_id) / "chat" / "global.ndjson"


def chat_threads_dir(project_id: str) -> Path:
    return project_dir(project_id) / "chat" / "threads"


def chat_thread_path(project_id: str, tag: str) -> Path:
    safe_tag = "".join(ch for ch in tag if ch.isalnum() or ch in {"-", "_"}).lower()
    return chat_threads_dir(project_id) / f"{safe_tag}.ndjson"


def append_chat_message(project_id: str, payload: dict[str, Any]) -> None:
    _append_ndjson(chat_global_path(project_id), payload)


def append_thread_message(project_id: str, tag: str, payload: dict[str, Any]) -> None:
    safe_tag = "".join(ch for ch in tag if ch.isalnum() or ch in {"-", "_"}).lower()
    if not safe_tag:
        return
    _append_ndjson(chat_thread_path(project_id, safe_tag), payload)


def run_requests_path(project_id: str) -> Path:
    return project_dir(project_id) / "runs" / "requests.ndjson"


def append_run_request(project_id: str, payload: dict[str, Any]) -> None:
    _append_ndjson(run_requests_path(project_id), payload)


def agent_journal_path(project_id: str, agent_id: str) -> Path:
    return project_dir(project_id) / "agents" / agent_id / "journal.ndjson"


def append_agent_journal(project_id: str, agent_id: str, payload: dict[str, Any]) -> None:
    _append_ndjson(agent_journal_path(project_id, agent_id), payload)


def load_agent_journal(project_id: str, agent_id: str, limit: int = 200) -> list[dict[str, Any]]:
    return _read_ndjson(agent_journal_path(project_id, agent_id), limit=limit)


def record_mentions(project_id: str, payload: dict[str, Any]) -> None:
    mentions = payload.get("mentions") or []
    if not mentions:
        return

    timestamp = payload.get("timestamp") or _utc_now_iso()
    author = payload.get("author") or payload.get("agent_id") or "operator"
    event = payload.get("event") or ""
    message_id = payload.get("message_id")
    text = payload.get("text") or payload.get("content") or ""
    tags = payload.get("tags") or []
    thread_id = payload.get("thread_id")
    context_ref_raw = payload.get("context_ref")
    context_ref: dict[str, Any] | None = None
    if isinstance(context_ref_raw, dict):
        context_ref = {
            "kind": str(context_ref_raw.get("kind") or "").strip() or "context",
            "id": str(context_ref_raw.get("id") or "").strip(),
            "title": str(context_ref_raw.get("title") or "").strip(),
            "source_path": str(context_ref_raw.get("source_path") or "").strip(),
            "source_uri": str(context_ref_raw.get("source_uri") or "").strip(),
            "selected_at": str(context_ref_raw.get("selected_at") or _utc_now_iso()),
        }

    project = get_project(project_id)
    updated = False

    source = "reminder" if event == "clems_reminder" else "mention"

    for mention in mentions:
        request_id_base = (
            str(timestamp)
            .replace(":", "")
            .replace("-", "")
            .replace("+", "")
            .replace("Z", "")
            .replace("T", "")
        )
        request_id = f"runreq_{request_id_base}_{mention}"
        if message_id:
            request_id = f"{request_id}_{message_id}"

        # Wave07 dedup guard: skip if request_id already exists in queue
        existing = _read_ndjson(run_requests_path(project_id))
        if any(str(e.get("request_id", "")) == request_id for e in existing):
            continue

        append_run_request(
            project_id,
            {
                "request_id": request_id,
                "project_id": project_id,
                "agent_id": mention,
                "status": "queued",
                "source": source,
                "created_at": timestamp,
                "context_ref": context_ref,
                "message": {
                    "message_id": message_id,
                    "thread_id": thread_id,
                    "author": author,
                    "text": text,
                    "tags": tags,
                    "mentions": mentions,
                    "context_ref": context_ref,
                },
            },
        )


        agent = next((a for a in project.agents if a.agent_id == mention), None)
        if agent is None:
            continue

        agent.status = "pinged"
        agent.heartbeat = timestamp
        updated = True

        append_agent_journal(
            project_id,
            mention,
            {
                "timestamp": timestamp,
                "event": "mention",
                "from": author,
                "message_id": message_id,
                "thread_id": thread_id,
                "text": text,
                "tags": tags,
            },
        )

    if updated:
        save_project(project)

    if author == "operator":
        ack_text = "Mentions: " + " ".join(f"@{m}" for m in mentions)
        append_chat_message(
            project_id,
            {
                "timestamp": _utc_now_iso(),
                "author": "system",
                "text": ack_text,
                "tags": [],
                "mentions": [],
                "event": "mention_ack",
            },
        )


def load_chat_global(project_id: str, limit: int = 200) -> list[dict[str, Any]]:
    return _read_ndjson(chat_global_path(project_id), limit=limit)


def load_chat_thread(project_id: str, tag: str, limit: int = 200) -> list[dict[str, Any]]:
    return _read_ndjson(chat_thread_path(project_id, tag), limit=limit)


def list_chat_threads(project_id: str) -> list[str]:
    threads_dir = chat_threads_dir(project_id)
    if not threads_dir.exists():
        return []
    tags = []
    for path in sorted(threads_dir.iterdir()):
        if path.is_file() and path.suffix == ".ndjson":
            tags.append(path.stem)
    return tags


def get_project(project_id: str) -> ProjectData:
    """
    Get project by ID, raising error if not found.
    Used by MCP server.
    """
    canonical_project_id = _canonical_project_id(project_id)
    pdir = project_dir(canonical_project_id)
    if not pdir.exists():
        raise ValueError(f"Project not found: {project_id}")
    return load_project(canonical_project_id)


def save_project(project: ProjectData) -> None:
    """
    Save project data back to disk.
    Updates agent states and settings.
    Used by MCP server.
    """
    pdir = project.path

    # Save settings
    settings_path = pdir / "settings.json"
    project.settings["updated_at"] = _utc_now_iso()
    settings_path.write_text(json.dumps(project.settings, indent=2), encoding="utf-8")

    # Save agent states
    registry_payload = _load_registry(project.project_id)
    for agent in project.agents:
        agent_dir = pdir / "agents" / agent.agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        state_path = agent_dir / "state.json"
        state_data = asdict(agent)
        state_data["updated_at"] = _utc_now_iso()
        state_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")

        registry_payload[agent.agent_id] = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "engine": _normalize_engine(agent.engine),
            "platform": _normalize_platform(agent.platform, _normalize_engine(agent.engine)),
            "level": _normalize_level(agent.level, default=2),
            "lead_id": agent.lead_id,
            "role": _normalize_role(agent.role, default="specialist"),
            "skills": _normalize_skills(agent.skills),
        }

    _write_registry(project.project_id, registry_payload)
