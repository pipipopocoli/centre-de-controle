#!/usr/bin/env python3
"""
Cockpit MCP Server
==================
MCP server for Antigravity / Cockpit integration.

Self-contained: reads and writes directly to the filesystem under
``control/projects/<project_id>/``.  No imports from ``app/``, ``server/``,
or any other local package.

Implements 7 core tools:
- cockpit.post_message
- cockpit.read_state
- cockpit.update_agent_state
- cockpit.request_run
- cockpit.get_quotas
- cockpit.list_skills_catalog
- cockpit.sync_skills
"""

import asyncio
import json
import logging
import os
import re
import secrets
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# MCP SDK (with graceful fallback for testing)
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    class Tool:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class TextContent:  # type: ignore[no-redef]
        def __init__(self, type: str, text: str) -> None:
            self.type = type
            self.text = text

    class Server:  # type: ignore[no-redef]
        def __init__(self, name: str) -> None:
            self.name = name
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        def call_tool(self):
            def decorator(func):
                return func
            return decorator

    def stdio_server():  # type: ignore[no-redef]
        class _Ctx:
            async def __aenter__(self):
                return (None, None)
            async def __aexit__(self, *a: Any):
                pass
        return _Ctx()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = Path("/tmp/cockpit_mcp_server.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("cockpit-mcp")

if not MCP_AVAILABLE:
    logger.warning("MCP SDK not installed - running in mock mode for testing")
    logger.warning("Install with: pip install mcp")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent          # control/
PROJECTS_ROOT = ROOT_DIR / "projects"
SKILLS_CATALOG_PATH = ROOT_DIR / "skills" / "catalog.json"

PHASES = ["Plan", "Implement", "Test", "Review", "Ship"]
PROJECT_ID_ERROR = "strict_project_routing_violation"

# ---------------------------------------------------------------------------
# Inline data model
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    agent_id: str
    name: str = ""
    engine: str = "AG"
    phase: str = "Plan"
    percent: int = 0
    eta_minutes: Optional[int] = None
    heartbeat: str = ""
    status: str = "idle"
    blockers: list[str] = field(default_factory=list)
    current_task: str = ""
    # extra fields preserved from disk
    _extra: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "agent_id": self.agent_id,
            "name": self.name,
            "engine": self.engine,
            "phase": self.phase,
            "percent": self.percent,
            "eta_minutes": self.eta_minutes,
            "heartbeat": self.heartbeat,
            "status": self.status,
            "blockers": self.blockers,
            "current_task": self.current_task,
        }
        d.update(self._extra)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        known = {
            "agent_id", "name", "engine", "phase", "percent",
            "eta_minutes", "heartbeat", "status", "blockers", "current_task",
        }
        kwargs = {k: data[k] for k in known if k in data}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(**kwargs, _extra=extra)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _project_path(project_id: str) -> Path:
    return PROJECTS_ROOT / project_id


def _list_projects() -> list[str]:
    if not PROJECTS_ROOT.is_dir():
        return []
    return sorted(
        p.name for p in PROJECTS_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _append_ndjson(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_settings(project_id: str) -> dict[str, Any]:
    return _read_json(_project_path(project_id) / "settings.json")


def _save_settings(project_id: str, settings: dict[str, Any]) -> None:
    settings["updated_at"] = _utc_now_iso()
    _write_json(_project_path(project_id) / "settings.json", settings)


def _load_agent_state(project_id: str, agent_id: str) -> Optional[AgentState]:
    path = _project_path(project_id) / "agents" / agent_id / "state.json"
    if not path.exists():
        return None
    return AgentState.from_dict(_read_json(path))


def _save_agent_state(project_id: str, agent: AgentState) -> None:
    path = _project_path(project_id) / "agents" / agent.agent_id / "state.json"
    data = agent.to_dict()
    data["updated_at"] = _utc_now_iso()
    _write_json(path, data)


def _list_agent_ids(project_id: str) -> list[str]:
    agents_dir = _project_path(project_id) / "agents"
    if not agents_dir.is_dir():
        return []
    ids = []
    for p in agents_dir.iterdir():
        if p.is_dir() and (p / "state.json").exists():
            ids.append(p.name)
    return sorted(ids)


def _append_journal(project_id: str, agent_id: str, record: dict[str, Any]) -> None:
    path = _project_path(project_id) / "agents" / agent_id / "journal.ndjson"
    _append_ndjson(path, record)


def _append_chat_global(project_id: str, record: dict[str, Any]) -> None:
    path = _project_path(project_id) / "chat" / "global.ndjson"
    _append_ndjson(path, record)


def _append_thread(project_id: str, thread_id: str, record: dict[str, Any]) -> None:
    path = _project_path(project_id) / "chat" / "threads" / f"{thread_id}.ndjson"
    _append_ndjson(path, record)


# ---------------------------------------------------------------------------
# Inline parse_mentions (replaces app.services.chat_parser)
# ---------------------------------------------------------------------------
_MENTION_RE = re.compile(r"@([\w.-]+)")


def parse_mentions(text: str) -> list[str]:
    """Extract unique @mentions from text."""
    return sorted(set(_MENTION_RE.findall(text)))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_phase(value: Any) -> str:
    if not value:
        return PHASES[0]
    raw = str(value).strip().lower()
    synonyms = {
        "planning": "Plan", "plan": "Plan", "init": "Plan", "initialization": "Plan",
        "implement": "Implement", "implementation": "Implement", "build": "Implement",
        "execute": "Implement", "executing": "Implement",
        "test": "Test", "testing": "Test", "qa": "Test",
        "verify": "Review", "verifying": "Review", "review": "Review",
        "ship": "Ship", "release": "Ship", "complete": "Ship",
        "completed": "Ship", "done": "Ship",
    }
    if raw in synonyms:
        return synonyms[raw]
    for option in PHASES:
        if option.lower() == raw:
            return option
    return PHASES[0]


def _normalize_engine(value: Any) -> str:
    if not value:
        return "AG"
    raw = str(value).strip().lower()
    if raw in {"ag", "antigravity", "anti-gravity"}:
        return "AG"
    if raw in {"cdx", "codex"}:
        return "CDX"
    return "AG"


def _normalize_percent(value: Any) -> int:
    try:
        percent = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(percent, 100))


def _normalize_blockers(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        trimmed = value.strip()
        return [trimmed] if trimmed else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _normalize_tags(tags: Any) -> list[str]:
    if not tags or not isinstance(tags, list):
        return []
    normalized: set[str] = set()
    for item in tags:
        if not isinstance(item, str):
            continue
        tag = item.strip()
        if tag.startswith("#"):
            tag = tag[1:]
        tag = tag.strip().lower()
        if tag:
            normalized.add(tag)
    return sorted(normalized)


def _new_message_id(agent_id: str) -> str:
    agent_fragment = str(agent_id or "agent")[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    suffix = secrets.token_hex(2)
    return f"msg_{ts}_{agent_fragment}_{suffix}"


def _infer_project_id(arguments: dict[str, Any]) -> Optional[str]:
    project_id = arguments.get("project_id")
    if isinstance(project_id, str) and project_id.strip():
        return project_id.strip()
    metadata = arguments.get("metadata", {})
    if isinstance(metadata, dict):
        project_id = metadata.get("project_id")
        if isinstance(project_id, str) and project_id.strip():
            return project_id.strip()
    env_pid = os.environ.get("COCKPIT_PROJECT_ID")
    if env_pid and env_pid.strip():
        return env_pid.strip()
    return None


# ---------------------------------------------------------------------------
# Initialize MCP server
# ---------------------------------------------------------------------------
server = Server("cockpit")

TOOL_DEFINITIONS = [
    Tool(
        name="cockpit.post_message",
        description="Post messages to Cockpit chatroom (global channel or specific threads)",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Message content (markdown supported)",
                    "maxLength": 4000,
                },
                "thread_id": {
                    "type": "string",
                    "description": "Optional thread ID. If null, posts to global channel",
                },
                "project_id": {
                    "type": "string",
                    "description": "Project identifier (preferred over metadata.project_id)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "default": "normal",
                    "description": "Message priority level",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for filtering/organization",
                    "maxItems": 5,
                },
                "agent_id": {
                    "type": "string",
                    "description": "Antigravity agent identifier",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional structured metadata",
                },
            },
            "required": ["content", "agent_id", "project_id"],
        },
    ),
    Tool(
        name="cockpit.read_state",
        description="Read current project state and roadmap information",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier. If null, returns all accessible projects",
                },
                "scope": {
                    "type": "string",
                    "enum": ["summary", "roadmap", "agents", "metrics", "full"],
                    "default": "summary",
                    "description": "Data scope to retrieve",
                },
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier",
                },
            },
            "required": ["agent_id"],
        },
    ),
    Tool(
        name="cockpit.update_agent_state",
        description="Signal agent progression (%, phase, ETA) to update the Cockpit grid",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Antigravity agent identifier",
                },
                "project_id": {
                    "type": "string",
                    "description": "Associated project",
                },
                "status": {
                    "type": "string",
                    "enum": ["idle", "planning", "executing", "verifying", "blocked", "error", "completed"],
                    "description": "Current agent status",
                },
                "progress": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Completion percentage of current task",
                },
                "percent": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Completion percentage (canonical; alias of progress)",
                },
                "current_phase": {
                    "type": "string",
                    "description": "Current work phase",
                },
                "phase": {
                    "type": "string",
                    "description": "Current phase (canonical; alias of current_phase)",
                },
                "current_task": {
                    "type": "string",
                    "description": "Brief description of current task",
                    "maxLength": 200,
                },
                "eta": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Estimated completion time",
                },
                "eta_minutes": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Estimated completion time in minutes (canonical)",
                },
                "engine": {
                    "type": "string",
                    "description": "Engine identifier for grid badge (canonical): CDX or AG",
                },
                "blockers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of blockers (canonical)",
                    "maxItems": 10,
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metrics",
                },
                "heartbeat": {
                    "type": "boolean",
                    "default": False,
                    "description": "True if this is a periodic heartbeat update",
                },
            },
            "required": ["agent_id", "project_id", "status"],
        },
    ),
    Tool(
        name="cockpit.request_run",
        description="Trigger runs with user confirmation",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier",
                },
                "run_type": {
                    "type": "string",
                    "enum": ["test", "build", "deploy", "analysis", "migration", "custom"],
                    "description": "Type of run to execute",
                },
                "project_id": {
                    "type": "string",
                    "description": "Target project",
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description",
                    "maxLength": 500,
                },
                "parameters": {
                    "type": "object",
                    "description": "Run-specific parameters",
                },
                "estimated_duration": {
                    "type": "integer",
                    "description": "Estimated duration in seconds",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["safe", "low", "medium", "high"],
                    "default": "low",
                    "description": "Risk assessment",
                },
                "requires_confirmation": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether user confirmation is required",
                },
            },
            "required": ["agent_id", "run_type", "project_id", "description"],
        },
    ),
    Tool(
        name="cockpit.get_quotas",
        description="Report quota and rate limit status",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier",
                },
                "scope": {
                    "type": "string",
                    "enum": ["agent", "project", "global"],
                    "default": "agent",
                    "description": "Quota scope to check",
                },
            },
            "required": ["agent_id"],
        },
    ),
    Tool(
        name="cockpit.list_skills_catalog",
        description="List curated skills catalog for a project with cache/fail-open metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier",
                },
                "project_id": {
                    "type": "string",
                    "description": "Target project",
                },
            },
            "required": ["agent_id", "project_id"],
        },
    ),
    Tool(
        name="cockpit.sync_skills",
        description="Sync curated skills for a project with dry_run support",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier",
                },
                "project_id": {
                    "type": "string",
                    "description": "Target project",
                },
                "desired_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional explicit list of skill ids. Defaults to full curated catalog.",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, computes actions without state mutation.",
                },
            },
            "required": ["agent_id", "project_id"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Skills catalog helpers (simplified, file-based)
# ---------------------------------------------------------------------------

def _load_skills_catalog() -> tuple[list[dict[str, Any]], str]:
    """Load skills catalog from ``control/skills/catalog.json``.

    Returns (catalog_list, source) where *source* is ``"file"`` when the file
    exists and ``"empty"`` otherwise.
    """
    if SKILLS_CATALOG_PATH.exists():
        try:
            data = json.loads(SKILLS_CATALOG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data, "file"
            if isinstance(data, dict) and "skills" in data:
                return data["skills"], "file"
        except Exception:
            pass
    return [], "empty"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def handle_post_message(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        content = arguments["content"]
        agent_id = arguments["agent_id"]
        thread_id = arguments.get("thread_id")
        priority = arguments.get("priority", "normal")
        tags = _normalize_tags(arguments.get("tags"))
        metadata = arguments.get("metadata", {})

        project_id_raw = arguments.get("project_id")
        project_id = project_id_raw.strip() if isinstance(project_id_raw, str) and project_id_raw.strip() else None
        metadata_project_id = None
        if isinstance(metadata, dict):
            meta_pid = metadata.get("project_id")
            if isinstance(meta_pid, str) and meta_pid.strip():
                metadata_project_id = meta_pid.strip()

        # Strict routing policy
        if not project_id:
            return [TextContent(type="text", text=json.dumps({"error": PROJECT_ID_ERROR}))]
        if metadata_project_id and metadata_project_id != project_id:
            return [TextContent(type="text", text=json.dumps({"error": PROJECT_ID_ERROR}))]

        message_id = _new_message_id(agent_id)
        timestamp = _utc_now_iso()

        mentions = parse_mentions(content)
        message_payload: dict[str, Any] = {
            "message_id": message_id,
            "timestamp": timestamp,
            "author": agent_id,
            "text": content,
            "thread_id": thread_id,
            "priority": priority,
            "tags": tags,
            "mentions": mentions,
            "metadata": metadata,
        }

        logger.info(f"Message posted: {message_id} from {agent_id} (project={project_id}, priority={priority})")

        # Write to global chat
        _append_chat_global(project_id, message_payload)

        # Write to tag-based threads
        for tag in tags:
            _append_thread(project_id, tag, message_payload)

        # Write to explicit thread
        if thread_id:
            _append_thread(project_id, str(thread_id), message_payload)

        # Record mentions in agent journals
        for mentioned in mentions:
            _append_journal(project_id, mentioned, {
                "type": "mention",
                "message_id": message_id,
                "from": agent_id,
                "timestamp": timestamp,
            })

        result = {
            "message_id": message_id,
            "timestamp": timestamp,
            "status": "posted",
            "thread_url": f"cockpit://messages/{message_id}",
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in post_message: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_read_state(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments.get("project_id")
        scope = arguments.get("scope", "summary")

        logger.info(f"Reading state: agent={agent_id}, project={project_id}, scope={scope}")

        if project_id:
            projects_data = [_serialize_project(project_id, scope)]
        else:
            projects_data = [_serialize_project(pid, scope) for pid in _list_projects()]

        result = {
            "projects": projects_data,
            "timestamp": _utc_now_iso(),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in read_state: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_update_agent_state(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments["project_id"]
        status = arguments["status"]
        percent_raw = arguments.get("percent", arguments.get("progress"))
        phase_raw = arguments.get("phase", arguments.get("current_phase", ""))
        current_task = arguments.get("current_task", "")
        eta = arguments.get("eta")
        eta_minutes_raw = arguments.get("eta_minutes")
        engine_raw = arguments.get("engine")
        blockers_raw = arguments.get("blockers")
        metadata = arguments.get("metadata", {})
        is_heartbeat = arguments.get("heartbeat", False)

        logger.info(f"Updating agent state: {agent_id} @ {project_id} - {status} ({percent_raw}%)")

        has_percent = "percent" in arguments or "progress" in arguments
        has_phase = "phase" in arguments or "current_phase" in arguments
        has_engine = (
            "engine" in arguments
            or (isinstance(metadata, dict) and ("engine" in metadata or "source" in metadata))
        )
        has_blockers = "blockers" in arguments
        has_eta = "eta_minutes" in arguments or "eta" in arguments

        # Resolve ETA minutes
        eta_minutes: Optional[int] = None
        if eta_minutes_raw is not None:
            try:
                eta_minutes = int(eta_minutes_raw)
            except (TypeError, ValueError):
                eta_minutes = None
        elif eta:
            try:
                eta_dt = datetime.fromisoformat(str(eta).replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                eta_minutes = int((eta_dt - now).total_seconds() / 60)
            except Exception as exc:
                logger.warning(f"Could not parse ETA: {exc}")

        # Resolve engine value from arguments or metadata
        resolved_engine = (
            engine_raw
            or (metadata.get("engine") if isinstance(metadata, dict) else None)
            or (metadata.get("source") if isinstance(metadata, dict) else None)
        )

        # Load or create agent state
        agent = _load_agent_state(project_id, agent_id)
        if agent is not None:
            agent.status = status
            agent.heartbeat = _utc_now_iso()
            if not is_heartbeat:
                if has_percent:
                    agent.percent = _normalize_percent(percent_raw)
                if has_phase and str(phase_raw).strip():
                    agent.phase = _normalize_phase(phase_raw)
                if has_engine:
                    agent.engine = _normalize_engine(resolved_engine)
                if has_blockers:
                    agent.blockers = _normalize_blockers(blockers_raw)
                if has_eta:
                    agent.eta_minutes = eta_minutes
                if current_task:
                    agent.current_task = current_task
        else:
            agent = AgentState(
                agent_id=agent_id,
                name=metadata.get("name", agent_id) if isinstance(metadata, dict) else agent_id,
                engine=_normalize_engine(resolved_engine or "AG"),
                phase=_normalize_phase(phase_raw) if str(phase_raw).strip() else PHASES[0],
                percent=_normalize_percent(percent_raw) if has_percent else 0,
                eta_minutes=eta_minutes,
                heartbeat=_utc_now_iso(),
                status=status,
                blockers=_normalize_blockers(blockers_raw) if has_blockers else [],
                current_task=current_task or "",
            )

        _save_agent_state(project_id, agent)

        # Store current task in project settings
        if not is_heartbeat:
            settings = _load_settings(project_id)
            if "agent_tasks" not in settings:
                settings["agent_tasks"] = {}
            settings["agent_tasks"][agent_id] = {
                "current_task": current_task,
                "current_phase": agent.phase,
                "metadata": metadata,
                "updated_at": _utc_now_iso(),
            }
            _save_settings(project_id, settings)

        # Append to agent journal
        _append_journal(project_id, agent_id, {
            "type": "state_update",
            "status": status,
            "phase": agent.phase,
            "percent": agent.percent,
            "current_task": current_task,
            "heartbeat": is_heartbeat,
            "timestamp": _utc_now_iso(),
        })

        update_id = f"update_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"
        result = {
            "update_id": update_id,
            "timestamp": _utc_now_iso(),
            "acknowledged": True,
            "dashboard_url": f"cockpit://projects/{project_id}/agents/{agent_id}",
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in update_agent_state: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_request_run(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        run_type = arguments["run_type"]
        project_id = arguments["project_id"]
        description = arguments["description"]
        parameters = arguments.get("parameters", {})
        estimated_duration = arguments.get("estimated_duration")
        risk_level = arguments.get("risk_level", "low")
        requires_confirmation = arguments.get("requires_confirmation", True)

        logger.info(f"Run request: {run_type} from {agent_id} (risk: {risk_level})")

        request_id = f"run_req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"

        auto_approved = risk_level == "safe" and run_type == "test" and not requires_confirmation
        status = "approved" if auto_approved else "pending_approval"
        run_id = f"run_{run_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}" if auto_approved else None

        # Persist run request in settings
        settings = _load_settings(project_id)
        if "run_requests" not in settings:
            settings["run_requests"] = []

        run_request = {
            "request_id": request_id,
            "run_id": run_id,
            "agent_id": agent_id,
            "run_type": run_type,
            "description": description,
            "parameters": parameters,
            "estimated_duration": estimated_duration,
            "risk_level": risk_level,
            "status": status,
            "created_at": _utc_now_iso(),
            "auto_approved": auto_approved,
        }
        settings["run_requests"].append(run_request)
        _save_settings(project_id, settings)

        result = {
            "request_id": request_id,
            "status": status,
            "run_id": run_id,
            "confirmation_url": f"cockpit://projects/{project_id}/runs/{request_id}",
            "estimated_approval_time": 300 if not auto_approved else 0,
            "message": "Auto-approved" if auto_approved else "Pending user confirmation",
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in request_run: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_get_quotas(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        scope = arguments.get("scope", "agent")

        logger.info(f"Checking quotas: agent={agent_id}, scope={scope}")

        result = {
            "quotas": {
                "api_calls": {
                    "limit": 10000,
                    "used": 150,
                    "remaining": 9850,
                    "reset_at": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat(),
                    "status": "OK",
                },
                "messages": {
                    "limit": 1000,
                    "used": 45,
                    "remaining": 955,
                    "reset_at": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat(),
                    "status": "OK",
                },
                "runs": {
                    "concurrent_limit": 5,
                    "active_runs": 0,
                    "queued_runs": 0,
                    "status": "OK",
                },
                "storage": {
                    "limit_bytes": 10737418240,
                    "used_bytes": 1073741824,
                    "remaining_bytes": 9663676416,
                    "status": "OK",
                },
            },
            "plan": "developer",
            "warnings": [],
            "timestamp": _utc_now_iso(),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in get_quotas: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_list_skills_catalog(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments["project_id"]
        logger.info(f"Listing skills catalog: agent={agent_id}, project={project_id}")

        catalog, source = _load_skills_catalog()

        payload = {
            "status": "ok" if catalog else "degraded",
            "project_id": project_id,
            "requested_by": agent_id,
            "source": source,
            "skill_count": len(catalog),
            "catalog": catalog,
            "warnings": [] if catalog else ["catalog empty or not found"],
            "cache_path": str(SKILLS_CATALOG_PATH),
            "timestamp": _utc_now_iso(),
        }
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    except Exception as e:
        logger.error(f"Error in list_skills_catalog: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_sync_skills(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments["project_id"]
        dry_run = bool(arguments.get("dry_run", False))
        desired_raw = arguments.get("desired_skills")
        desired_skills: list[str] = desired_raw if isinstance(desired_raw, list) else []

        logger.info(
            "Sync skills request: agent=%s project=%s dry_run=%s desired=%s",
            agent_id, project_id, dry_run, len(desired_skills),
        )

        catalog, source = _load_skills_catalog()

        # Extract IDs from catalog
        catalog_ids: list[str] = []
        for entry in catalog:
            if isinstance(entry, dict):
                skill_id = str(entry.get("id") or "").strip()
                if skill_id:
                    catalog_ids.append(skill_id)

        requested = [str(s).strip() for s in desired_skills if str(s).strip()]
        if not requested:
            requested = sorted(set(catalog_ids))

        # Simple allow-all policy (catalog is the source of truth)
        catalog_id_set = set(catalog_ids)
        allowed = [sid for sid in requested if sid in catalog_id_set] if catalog_id_set else requested
        rejected = [sid for sid in requested if sid not in catalog_id_set] if catalog_id_set else []

        actions: list[dict[str, str]] = []
        if not dry_run:
            # Persist the desired skills list in project settings
            settings = _load_settings(project_id)
            settings["synced_skills"] = allowed
            settings["synced_skills_at"] = _utc_now_iso()
            _save_settings(project_id, settings)
            for sid in allowed:
                actions.append({"action": "install", "skill_id": sid, "status": "ok"})
        else:
            for sid in allowed:
                actions.append({"action": "install", "skill_id": sid, "status": "dry_run"})

        payload = {
            "status": "ok",
            "project_id": project_id,
            "requested_by": agent_id,
            "dry_run": dry_run,
            "requested_skills": requested,
            "allowed_skills": allowed,
            "rejected_skills": rejected,
            "actions": actions,
            "catalog_source": source,
            "catalog_warnings": [] if catalog else ["catalog empty or not found"],
            "cache_path": str(SKILLS_CATALOG_PATH),
            "timestamp": _utc_now_iso(),
        }
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    except Exception as e:
        logger.error(f"Error in sync_skills: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ---------------------------------------------------------------------------
# Project serialization for read_state
# ---------------------------------------------------------------------------

def _serialize_project(project_id: str, scope: str) -> dict[str, Any]:
    """Serialize project data from the filesystem based on scope."""
    ppath = _project_path(project_id)
    settings = _load_settings(project_id)

    data: dict[str, Any] = {
        "project_id": project_id,
        "name": settings.get("project_name", project_id),
        "status": settings.get("status", "active"),
    }

    if scope in ("roadmap", "full"):
        roadmap_text = _read_text(ppath / "ROADMAP.md")
        data["roadmap"] = {
            "phases": [
                {
                    "phase_id": phase,
                    "name": phase,
                    "status": "active" if i < 2 else "pending",
                    "progress": 0,
                    "eta": None,
                }
                for i, phase in enumerate(PHASES)
            ],
            "current_phase": PHASES[0],
            "raw": roadmap_text[:4000] if roadmap_text else None,
        }

    if scope in ("agents", "full"):
        agents_list: list[dict[str, Any]] = []
        for aid in _list_agent_ids(project_id):
            agent = _load_agent_state(project_id, aid)
            if agent is None:
                continue
            agents_list.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "engine": agent.engine,
                "phase": agent.phase,
                "percent": agent.percent,
                "eta_minutes": agent.eta_minutes,
                "heartbeat": agent.heartbeat,
                "status": agent.status or "idle",
                "blockers": agent.blockers,
                "current_task": (
                    settings.get("agent_tasks", {}).get(aid, {}).get("current_task")
                    or agent.current_task
                ),
            })
        data["agents"] = agents_list

    if scope in ("metrics", "full"):
        run_requests = settings.get("run_requests", [])
        agent_count = len(_list_agent_ids(project_id))
        data["metrics"] = {
            "total_agents": agent_count,
            "active_runs": len([r for r in run_requests if r.get("status") == "running"]),
            "pending_runs": len([r for r in run_requests if r.get("status") == "pending_approval"]),
            "last_update": _utc_now_iso(),
        }

    if scope == "full":
        state_text = _read_text(ppath / "STATE.md")
        if state_text:
            data["state_raw"] = state_text[:4000]

    return data


# ---------------------------------------------------------------------------
# MCP Server handlers
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOL_DEFINITIONS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    logger.info(f"Tool called: {name}")

    handlers = {
        "cockpit.post_message": handle_post_message,
        "cockpit.read_state": handle_read_state,
        "cockpit.update_agent_state": handle_update_agent_state,
        "cockpit.request_run": handle_request_run,
        "cockpit.get_quotas": handle_get_quotas,
        "cockpit.list_skills_catalog": handle_list_skills_catalog,
        "cockpit.sync_skills": handle_sync_skills,
    }

    handler = handlers.get(name)
    if handler:
        return await handler(arguments)
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    logger.info("Starting Cockpit MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
