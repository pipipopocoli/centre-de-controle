from __future__ import annotations

import json
import re
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
    {"agent_id": "clems", "name": "Clems", "engine": "CDX"},
    {"agent_id": "victor", "name": "Victor", "engine": "CDX"},
    {"agent_id": "leo", "name": "Leo", "engine": "AG"},
]

AGENT_NUMBER_RE = re.compile(r"^agent-(\d+)$")


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


def agent_registry_path(project_id: str) -> Path:
    return project_dir(project_id) / "agents" / "registry.json"


def _default_engine_for_agent(agent_id: str) -> str:
    lowered = str(agent_id or "").strip().lower()
    if lowered == "leo":
        return "AG"
    if lowered in {"clems", "victor"}:
        return "CDX"
    match = AGENT_NUMBER_RE.match(lowered)
    if not match:
        return "CDX"
    try:
        number = int(match.group(1))
    except ValueError:
        return "CDX"
    return "CDX" if number % 2 == 1 else "AG"


def _default_agent_name(agent_id: str) -> str:
    lowered = str(agent_id or "").strip().lower()
    for entry in DEFAULT_AGENT_ROSTER:
        if entry["agent_id"] == lowered:
            return entry["name"]
    if lowered.startswith("agent-"):
        return lowered
    return lowered.title() if lowered else "agent"


def _default_agent_registry_entry(
    agent_id: str,
    *,
    name: str | None = None,
    engine: str | None = None,
) -> dict[str, Any]:
    lowered = str(agent_id or "").strip().lower()
    level = 2
    lead_id = "victor"
    role = "specialist"
    if lowered == "clems":
        level = 0
        lead_id = None
        role = "orchestrator"
    elif lowered == "victor":
        level = 1
        lead_id = "clems"
        role = "backend_lead"
    elif lowered == "leo":
        level = 1
        lead_id = "clems"
        role = "ui_lead"
    else:
        match = AGENT_NUMBER_RE.match(lowered)
        if match:
            number = int(match.group(1))
            lead_id = "victor" if (number % 2 == 1) else "leo"

    return {
        "agent_id": lowered,
        "name": str(name).strip() if name else _default_agent_name(lowered),
        "engine": _normalize_engine(engine or _default_engine_for_agent(lowered)),
        "level": level,
        "lead_id": lead_id,
        "role": role,
    }


def _normalize_level(value: Any, fallback: int) -> int:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return fallback
    if level < 0:
        return 0
    if level > 2:
        return 2
    return level


def _normalize_registry_entry(agent_id: str, payload: Any) -> dict[str, Any]:
    entry = _default_agent_registry_entry(agent_id)
    if isinstance(payload, dict):
        if payload.get("name"):
            entry["name"] = str(payload.get("name")).strip() or entry["name"]
        entry["engine"] = _normalize_engine(payload.get("engine") or entry["engine"])
        entry["level"] = _normalize_level(payload.get("level"), entry["level"])
        role = str(payload.get("role") or "").strip()
        if role:
            entry["role"] = role
        lead_raw = payload.get("lead_id")
        lead_id = str(lead_raw).strip() if lead_raw is not None else ""
        entry["lead_id"] = lead_id or None

    if entry["level"] == 0:
        entry["lead_id"] = None
    elif not entry["lead_id"]:
        entry["lead_id"] = _default_agent_registry_entry(agent_id)["lead_id"]
    return entry


def _load_agent_registry(project_id: str) -> dict[str, dict[str, Any]]:
    path = agent_registry_path(project_id)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    registry: dict[str, dict[str, Any]] = {}
    for agent_id, entry in payload.items():
        key = str(agent_id).strip().lower()
        if not key:
            continue
        registry[key] = _normalize_registry_entry(key, entry)
    return registry


def _save_agent_registry(project_id: str, registry: dict[str, dict[str, Any]]) -> None:
    path = agent_registry_path(project_id)
    normalized: dict[str, dict[str, Any]] = {}
    for agent_id in sorted(registry.keys()):
        key = str(agent_id).strip().lower()
        if not key:
            continue
        normalized[key] = _normalize_registry_entry(key, registry.get(key))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")


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
        "automation": {
            "execution_mode": "codex_headless_ag_supervised",
            "codex": {
                "enabled": True,
            },
            "antigravity": {
                "enabled": True,
                "supervised_only": True,
                "mode": "agent",
                "reuse_window": True,
                "cli_path": "/Applications/Antigravity.app/Contents/Resources/app/bin/antigravity",
            },
            "timeouts": {
                "codex_seconds": 900,
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


def ensure_demo_project() -> ProjectData:
    ensure_project_structure("demo", "Demo")
    return load_project("demo")


def list_projects() -> list[str]:
    if not PROJECTS_DIR.exists():
        return []
    return sorted([p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()])


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
    # Canonical engines for the grid are CDX/AG; default unknown to AG.
    return "AG"


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


def ensure_agent_files(project_id: str, agent_id: str, name: str, engine: str) -> None:
    agent_dir = project_dir(project_id) / "agents" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    registry_entry = _normalize_registry_entry(
        agent_id,
        {
            "name": name,
            "engine": engine,
        },
    )

    state_path = agent_dir / "state.json"
    _write_json_if_missing(
        state_path,
        {
            "agent_id": agent_id,
            "name": registry_entry["name"],
            "engine": registry_entry["engine"],
            "phase": PHASES[0],
            "percent": 0,
            "eta_minutes": None,
            "heartbeat": _utc_now_iso(),
            "status": "idle",
            "blockers": [],
            "current_task": "",
            "level": registry_entry["level"],
            "lead_id": registry_entry["lead_id"],
            "role": registry_entry["role"],
        },
    )
    _write_text_if_missing(agent_dir / "journal.ndjson", "")
    _write_text_if_missing(agent_dir / "memory.md", _memory_template(agent_id))


def ensure_default_roster(project_id: str) -> None:
    agents_dir = project_dir(project_id) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry = _load_agent_registry(project_id)
    for agent in DEFAULT_AGENT_ROSTER:
        ensure_agent_files(
            project_id=project_id,
            agent_id=agent["agent_id"],
            name=agent["name"],
            engine=agent["engine"],
        )
        key = agent["agent_id"].strip().lower()
        registry[key] = _normalize_registry_entry(key, registry.get(key) or agent)
    _save_agent_registry(project_id, registry)


def load_project(project_id: str) -> ProjectData:
    pdir = project_dir(project_id)
    if pdir.exists():
        ensure_default_roster(project_id)
    registry = _load_agent_registry(project_id)
    registry_dirty = False
    settings_path = pdir / "settings.json"
    settings: dict[str, Any] = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    project_name = settings.get("project_name", project_id.title())

    agents: list[AgentState] = []
    agents_dir = pdir / "agents"
    if agents_dir.exists():
        for agent_folder in sorted([p for p in agents_dir.iterdir() if p.is_dir()]):
            agent_key = agent_folder.name.strip().lower()
            state_path = agent_folder / "state.json"
            if not state_path.exists():
                continue
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            registry_entry = registry.get(agent_key)
            if registry_entry is None:
                registry_entry = _normalize_registry_entry(agent_key, payload)
                registry[agent_key] = registry_entry
                registry_dirty = True

            settings_tasks = settings.get("agent_tasks") if isinstance(settings, dict) else {}
            task_entry = settings_tasks.get(agent_folder.name) if isinstance(settings_tasks, dict) else None
            current_task = None
            if isinstance(task_entry, dict):
                current_task = task_entry.get("current_task")
            if current_task is None:
                current_task = payload.get("current_task")

            agents.append(
                AgentState(
                    agent_id=payload.get("agent_id", agent_folder.name),
                    name=payload.get("name") or registry_entry.get("name") or _default_agent_name(agent_key),
                    engine=_normalize_engine(
                        payload.get("engine") or payload.get("source") or registry_entry.get("engine")
                    ),
                    phase=_normalize_phase(payload.get("phase")),
                    percent=_normalize_percent(payload.get("percent", payload.get("progress", 0))),
                    eta_minutes=_normalize_eta(payload.get("eta_minutes")),
                    heartbeat=payload.get("heartbeat"),
                    status=payload.get("status"),
                    blockers=_normalize_blockers(payload.get("blockers")),
                    current_task=str(current_task).strip() if current_task else None,
                    level=_normalize_level(payload.get("level"), int(registry_entry.get("level", 2))),
                    lead_id=(
                        str(payload.get("lead_id")).strip()
                        if payload.get("lead_id") is not None and str(payload.get("lead_id")).strip()
                        else registry_entry.get("lead_id")
                    ),
                    role=(
                        str(payload.get("role")).strip()
                        if payload.get("role") is not None and str(payload.get("role")).strip()
                        else registry_entry.get("role")
                    ),
                )
            )

    if registry_dirty:
        _save_agent_registry(project_id, registry)

    roadmap_md = _parse_markdown_roadmap(pdir / "ROADMAP.md")
    if any(roadmap_md.values()):
        roadmap = roadmap_md
    else:
        roadmap = _parse_simple_roadmap(pdir / "roadmap.yml")

    return ProjectData(
        project_id=project_id,
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


def mark_agent_requests_done(project_id: str, agent_id: str, responded_at: str | None = None) -> int:
    """
    Mark the most recent open run request for an agent as replied/closed in requests.ndjson.

    This keeps lifecycle files coherent for UI pending counters and reminders.
    """
    path = run_requests_path(project_id)
    if not path.exists():
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0

    now_iso = responded_at or _utc_now_iso()
    target_agent = str(agent_id or "").strip()
    if not target_agent:
        return 0

    updated = 0
    # newest first: close only one open request per reply to avoid collapsing history.
    for index in range(len(lines) - 1, -1, -1):
        raw = lines[index].strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue

        if str(payload.get("agent_id") or "").strip() != target_agent:
            continue

        status = str(payload.get("status") or "").strip().lower()
        if status not in {"queued", "dispatched", "reminded"}:
            continue

        payload["status"] = "closed"
        payload["responded_at"] = now_iso
        payload["closed_at"] = payload.get("closed_at") or now_iso
        payload["closed_reason"] = payload.get("closed_reason") or "reply_received"
        lines[index] = json.dumps(payload)
        updated = 1
        break

    if updated:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return updated


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
    lowered_text = str(text).lower()

    # Never fan out relayed auto-mode envelopes back into run requests.
    if "[cockpit auto-mode]" in lowered_text and "project lock:" in lowered_text:
        return

    project = get_project(project_id)
    updated = False

    source = "reminder" if event == "clems_reminder" else "mention"

    for mention in mentions:
        if str(mention).strip().lower() == "clems":
            # Clems is internal orchestrator; no external run request.
            continue
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

        append_run_request(
            project_id,
            {
                "request_id": request_id,
                "project_id": project_id,
                "agent_id": mention,
                "status": "queued",
                "source": source,
                "created_at": timestamp,
                "message": {
                    "message_id": message_id,
                    "thread_id": thread_id,
                    "author": author,
                    "text": text,
                    "tags": tags,
                    "mentions": mentions,
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
    pdir = project_dir(project_id)
    if not pdir.exists():
        raise ValueError(f"Project not found: {project_id}")
    return load_project(project_id)


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
    
    # Save agent states and registry metadata
    registry = _load_agent_registry(project.project_id)
    for agent in project.agents:
        agent_dir = pdir / "agents" / agent.agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        fallback = _default_agent_registry_entry(
            agent.agent_id,
            name=agent.name,
            engine=agent.engine,
        )
        level = _normalize_level(agent.level, int(fallback["level"]))
        lead_id = str(agent.lead_id).strip() if agent.lead_id else None
        role = str(agent.role).strip() if agent.role else str(fallback["role"])
        if level == 0:
            lead_id = None
        if level > 0 and not lead_id:
            lead_id = str(fallback["lead_id"]) if fallback["lead_id"] is not None else None

        agent.level = level
        agent.lead_id = lead_id
        agent.role = role

        state_path = agent_dir / "state.json"
        state_data = asdict(agent)
        state_data["updated_at"] = _utc_now_iso()
        state_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")

        key = str(agent.agent_id).strip().lower()
        registry[key] = _normalize_registry_entry(
            key,
            {
                "name": agent.name,
                "engine": agent.engine,
                "level": agent.level,
                "lead_id": agent.lead_id,
                "role": agent.role,
            },
        )
    _save_agent_registry(project.project_id, registry)
