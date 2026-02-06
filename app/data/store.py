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
    {"agent_id": "clems", "name": "Clems", "engine": "CDX"},
    {"agent_id": "victor", "name": "Victor", "engine": "CDX"},
    {"agent_id": "leo", "name": "Leo", "engine": "AG"},
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

    state_path = agent_dir / "state.json"
    _write_json_if_missing(
        state_path,
        {
            "agent_id": agent_id,
            "name": name,
            "engine": engine,
            "phase": PHASES[0],
            "percent": 0,
            "eta_minutes": None,
            "heartbeat": _utc_now_iso(),
            "status": "idle",
            "blockers": [],
        },
    )
    _write_text_if_missing(agent_dir / "journal.ndjson", "")
    _write_text_if_missing(agent_dir / "memory.md", _memory_template(agent_id))


def ensure_default_roster(project_id: str) -> None:
    agents_dir = project_dir(project_id) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for agent in DEFAULT_AGENT_ROSTER:
        ensure_agent_files(
            project_id=project_id,
            agent_id=agent["agent_id"],
            name=agent["name"],
            engine=agent["engine"],
        )


def load_project(project_id: str) -> ProjectData:
    pdir = project_dir(project_id)
    if pdir.exists():
        ensure_default_roster(project_id)
    settings_path = pdir / "settings.json"
    settings: dict[str, Any] = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    project_name = settings.get("project_name", project_id.title())

    agents: list[AgentState] = []
    agents_dir = pdir / "agents"
    if agents_dir.exists():
        for agent_folder in sorted([p for p in agents_dir.iterdir() if p.is_dir()]):
            state_path = agent_folder / "state.json"
            if not state_path.exists():
                continue
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            agents.append(
                AgentState(
                    agent_id=payload.get("agent_id", agent_folder.name),
                    name=payload.get("name", agent_folder.name.title()),
                    engine=_normalize_engine(payload.get("engine") or payload.get("source")),
                    phase=_normalize_phase(payload.get("phase")),
                    percent=_normalize_percent(payload.get("percent", payload.get("progress", 0))),
                    eta_minutes=_normalize_eta(payload.get("eta_minutes")),
                    heartbeat=payload.get("heartbeat"),
                    status=payload.get("status"),
                    blockers=_normalize_blockers(payload.get("blockers")),
                )
            )

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
    
    # Save agent states
    for agent in project.agents:
        agent_dir = pdir / "agents" / agent.agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        state_path = agent_dir / "state.json"
        state_data = asdict(agent)
        state_data["updated_at"] = _utc_now_iso()
        state_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
