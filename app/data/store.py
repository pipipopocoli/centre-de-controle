from __future__ import annotations

import json
import shutil
import sys
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
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except PermissionError:
        print(f"Warning: Permission denied for {path}. Assuming existing or read-only.")
    except Exception as e:
        print(f"Error handling {path}: {e}")


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


def _normalize_status(status: Any) -> str:
    if status is None:
        return "idle"
    raw = str(status).strip().lower()
    if not raw:
        return "idle"
    synonyms = {
        "running": "executing",
        "working": "executing",
        "in progress": "executing",
        "in_progress": "executing",
        "complete": "done",
        "completed": "done",
        "ok": "active",
        "stuck": "blocked",
        "failed": "error",
        "ping": "pinged",
        "reply": "replied",
    }
    normalized = synonyms.get(raw, raw)
    allowed = {"idle", "executing", "active", "blocked", "replied", "pinged", "done", "error"}
    if normalized in allowed:
        return normalized
    return "idle"


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
            "current_task": "",
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

            try:
                state_path = agent_folder / "state.json"
                if not state_path.exists():
                    continue

                payload = json.loads(state_path.read_text(encoding="utf-8"))
                
                # Check settings overrides for tasks
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
                        name=payload.get("name", agent_folder.name.title()),
                        engine=_normalize_engine(payload.get("engine") or payload.get("source")),
                        phase=_normalize_phase(payload.get("phase")),
                        percent=_normalize_percent(payload.get("percent", payload.get("progress", 0))),
                        status=_normalize_status(payload.get("status")),
                        current_task=str(current_task).strip() if current_task else None,
                        eta_minutes=_normalize_eta(payload.get("eta_minutes")),
                        heartbeat=payload.get("last_heartbeat") or payload.get("updated_at") or payload.get("heartbeat"),
                        blockers=_normalize_blockers(payload.get("blockers")),
                    )
                )
            except Exception as e:
                print(f"Skipping agent {agent_folder.name}: {e}")
                continue

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


def _read_ndjson(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    try:
        if not path.exists():
            return []
        
        lines = path.read_text(encoding="utf-8").splitlines()
        data = []
        for line in lines:
            if not line.strip():
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if limit and len(data) > limit:
            return data[-limit:]
        return data
    except (PermissionError, Exception) as e:
        print(f"Warning: Failed to read ndjson {path}: {e}")
        return []


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except PermissionError:
        print(f"Warning: Permission denied writing to {path}. Skipping append.")
    except Exception as e:
        print(f"Error appending to {path}: {e}")


def _write_text_if_missing(path: Path, content: str) -> None:
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    except PermissionError:
        print(f"Warning: Permission denied for {path}. Assuming existing or read-only.")
    except Exception as e:
        print(f"Error handling {path}: {e}")


def _write_ndjson_atomic(path: Path, payloads: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload) + "\n")
    tmp_path.replace(path)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


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


def load_run_requests(project_id: str) -> list[dict[str, Any]]:
    return _read_ndjson(run_requests_path(project_id), limit=0)


def mark_agent_requests_done(project_id: str, agent_id: str, responded_at: str | None = None) -> int:
    requests = load_run_requests(project_id)
    if not requests:
        return 0

    handled_at = responded_at or _utc_now_iso()
    responded_dt = _parse_iso(responded_at)
    changed = 0

    for payload in requests:
        if str(payload.get("agent_id") or "").strip() != agent_id:
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in {"done", "acknowledged"}:
            continue

        created_dt = _parse_iso(str(payload.get("created_at") or ""))
        if responded_dt and created_dt and created_dt > responded_dt:
            continue

        payload["status"] = "done"
        payload["handled_at"] = handled_at
        changed += 1

    if changed:
        _write_ndjson_atomic(run_requests_path(project_id), requests)
    return changed


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
    
    # Save agent states
    for agent in project.agents:
        agent_dir = pdir / "agents" / agent.agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        state_path = agent_dir / "state.json"
        state_data = asdict(agent)
        state_data["updated_at"] = _utc_now_iso()
        state_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
