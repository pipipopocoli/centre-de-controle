from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server.contracts import DecisionADR, ProjectStateSections, ProjectSummary, RoadmapSections
from server.security import hash_password


DEFAULT_AGENTS = [
    {
        "agent_id": "clems",
        "name": "Clems",
        "engine": "CDX",
        "platform": "codex",
        "level": 0,
        "lead_id": None,
        "role": "orchestrator",
    },
    {
        "agent_id": "victor",
        "name": "Victor",
        "engine": "CDX",
        "platform": "codex",
        "level": 1,
        "lead_id": "clems",
        "role": "backend_lead",
    },
    {
        "agent_id": "leo",
        "name": "Leo",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "ui_lead",
    },
    {
        "agent_id": "nova",
        "name": "Nova",
        "engine": "CDX",
        "platform": "codex",
        "level": 1,
        "lead_id": "clems",
        "role": "creative_science_lead",
    },
    {
        "agent_id": "vulgarisation",
        "name": "Vulgarisation",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "vulgarisation_lead",
    },
]

DEFAULT_LLM_PROFILE = {
    "voice_stt_model": "google/gemini-2.5-flash",
    "l1_model": "liquid/lfm-2.5-1.2b-thinking:free",
    "l2_scene_model": "arcee-ai/trinity-large-preview:free",
    "lfm_spawn_max": 10,
    "stream_enabled": True,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_ndjson(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    if limit > 0:
        rows = rows[-limit:]
    return rows


def _safe_project_id(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip().lower()).strip("-")
    if not token:
        raise ValueError("invalid project_id")
    return token


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ProjectRepository:
    def __init__(self, projects_root: Path) -> None:
        self.projects_root = Path(projects_root).expanduser()
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        return self.projects_root / _safe_project_id(project_id)

    def project_path(self, project_id: str) -> Path:
        path = self._project_dir(project_id)
        if not path.exists():
            raise FileNotFoundError(f"project not found: {project_id}")
        return path

    def _settings_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "settings.json"

    def _state_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "STATE.md"

    def _roadmap_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "ROADMAP.md"

    def _decisions_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "DECISIONS.md"

    def _agents_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "agents"

    def _chat_global_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "chat" / "global.ndjson"

    def _runs_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "runs"

    def _bmad_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "BMAD"

    def _ensure_project(self, project_id: str, name: str) -> Path:
        project_dir = self._project_dir(project_id)
        (project_dir / "chat" / "threads").mkdir(parents=True, exist_ok=True)
        (project_dir / "runs").mkdir(parents=True, exist_ok=True)
        (project_dir / "BMAD").mkdir(parents=True, exist_ok=True)
        settings_path = self._settings_path(project_id)
        if not settings_path.exists():
            _write_json(
                settings_path,
                {
                    "project_id": project_id,
                    "project_name": name,
                    "linked_repo_path": "",
                    "llm_profile": dict(DEFAULT_LLM_PROFILE),
                    "updated_at": _utc_now_iso(),
                },
            )
        if not self._state_path(project_id).exists():
            self.write_state_sections(
                project_id,
                ProjectStateSections(
                    phase="Plan",
                    objective="Bootstrap cloud API parity",
                    now=["Initialize project data"],
                    next=["Connect desktop and android clients"],
                ),
            )
        if not self._roadmap_path(project_id).exists():
            self.write_roadmap_sections(
                project_id,
                RoadmapSections(
                    now=["Cloud API foundation"],
                    next=["Desktop and Android parity"],
                    risks=["Legacy local-file drift"],
                ),
            )
        if not self._decisions_path(project_id).exists():
            self._decisions_path(project_id).write_text("# Decisions\n\n", encoding="utf-8")
        agents_dir = self._agents_dir(project_id)
        agents_dir.mkdir(parents=True, exist_ok=True)
        for item in DEFAULT_AGENTS:
            state_path = agents_dir / item["agent_id"] / "state.json"
            if state_path.exists():
                continue
            _write_json(
                state_path,
                {
                    **item,
                    "phase": "Plan",
                    "status": "idle",
                    "percent": 0,
                    "eta_minutes": None,
                    "blockers": [],
                    "current_task": "",
                    "heartbeat": _utc_now_iso(),
                    "updated_at": _utc_now_iso(),
                },
            )
        return project_dir

    def list_projects(self) -> list[ProjectSummary]:
        output: list[ProjectSummary] = []
        for entry in sorted(self.projects_root.iterdir(), key=lambda p: p.name):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue
            settings = _read_json(entry / "settings.json", {})
            if not isinstance(settings, dict):
                settings = {}
            project_id = str(settings.get("project_id") or entry.name)
            output.append(
                ProjectSummary(
                    project_id=project_id,
                    name=str(settings.get("project_name") or project_id.title()),
                    linked_repo_path=str(settings.get("linked_repo_path") or "") or None,
                    path=str(entry),
                    updated_at=str(settings.get("updated_at") or None),
                )
            )
        return output

    def create_project(self, *, project_id: str, name: str, linked_repo_path: str | None = None) -> ProjectSummary:
        normalized = _safe_project_id(project_id)
        self._ensure_project(normalized, name)
        settings = self.get_settings(normalized)
        settings["project_name"] = name
        settings["project_id"] = normalized
        settings["updated_at"] = _utc_now_iso()
        if linked_repo_path is not None:
            settings["linked_repo_path"] = linked_repo_path
        self.write_settings(normalized, settings)
        return self.get_project(normalized)

    def get_project(self, project_id: str) -> ProjectSummary:
        normalized = _safe_project_id(project_id)
        project_dir = self._project_dir(normalized)
        if not project_dir.exists():
            raise FileNotFoundError(f"project not found: {project_id}")
        settings = self.get_settings(normalized)
        return ProjectSummary(
            project_id=normalized,
            name=str(settings.get("project_name") or normalized.title()),
            linked_repo_path=str(settings.get("linked_repo_path") or "") or None,
            path=str(project_dir),
            updated_at=str(settings.get("updated_at") or None),
        )

    def get_settings(self, project_id: str) -> dict[str, Any]:
        data = _read_json(self._settings_path(project_id), {})
        return data if isinstance(data, dict) else {}

    def write_settings(self, project_id: str, payload: dict[str, Any]) -> None:
        payload["updated_at"] = _utc_now_iso()
        _write_json(self._settings_path(project_id), payload)

    def read_llm_profile(self, project_id: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        settings = self.get_settings(project_id)
        profile = settings.get("llm_profile")
        payload = profile if isinstance(profile, dict) else {}
        merged = dict(DEFAULT_LLM_PROFILE)
        if isinstance(defaults, dict):
            merged.update({key: value for key, value in defaults.items() if value is not None})
        merged.update({key: value for key, value in payload.items() if value is not None})
        merged["lfm_spawn_max"] = max(1, min(_safe_int(merged.get("lfm_spawn_max"), 10), 10))
        merged["stream_enabled"] = bool(merged.get("stream_enabled", True))
        return merged

    def write_llm_profile(self, project_id: str, payload: dict[str, Any], defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        settings = self.get_settings(project_id)
        merged = self.read_llm_profile(project_id, defaults=defaults)
        merged.update({key: value for key, value in payload.items() if value is not None})
        merged["lfm_spawn_max"] = max(1, min(_safe_int(merged.get("lfm_spawn_max"), 10), 10))
        merged["stream_enabled"] = bool(merged.get("stream_enabled", True))
        settings["llm_profile"] = merged
        self.write_settings(project_id, settings)
        return merged

    def linked_repo_path(self, project_id: str) -> str | None:
        settings = self.get_settings(project_id)
        value = str(settings.get("linked_repo_path") or "").strip()
        return value or None

    def _parse_section_bullets(self, text: str, section: str) -> list[str]:
        lines = str(text).splitlines()
        target = f"## {section}"
        in_section = False
        output: list[str] = []
        for raw in lines:
            stripped = raw.strip()
            if stripped.startswith("## "):
                in_section = stripped == target
                continue
            if not in_section:
                continue
            if stripped.startswith("# "):
                break
            if stripped.startswith("- "):
                token = stripped[2:].strip()
                if token:
                    output.append(token)
        return output

    def read_state_sections(self, project_id: str) -> ProjectStateSections:
        text = _read_text(self._state_path(project_id))
        return ProjectStateSections(
            phase=(self._parse_section_bullets(text, "Phase") or ["Plan"])[0],
            objective=" ".join(self._parse_section_bullets(text, "Objective")) or "TBD",
            now=self._parse_section_bullets(text, "Now"),
            next=self._parse_section_bullets(text, "Next"),
            in_progress=self._parse_section_bullets(text, "In Progress"),
            blockers=self._parse_section_bullets(text, "Blockers"),
            risks=self._parse_section_bullets(text, "Risks"),
            links=self._parse_section_bullets(text, "Links"),
        )

    def write_state_sections(self, project_id: str, sections: ProjectStateSections) -> None:
        payload = sections.model_dump()
        lines = [
            "# State",
            "",
            "## Phase",
            f"- {payload['phase']}",
            "",
            "## Objective",
            f"- {payload['objective']}",
            "",
            "## Now",
        ]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("now")) or ["none"])]
        lines += ["", "## Next"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("next")) or ["none"])]
        lines += ["", "## In Progress"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("in_progress")) or ["none"])]
        lines += ["", "## Blockers"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("blockers")) or ["none"])]
        lines += ["", "## Risks"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("risks")) or ["none"])]
        lines += ["", "## Links"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("links")) or ["none"])]
        lines.append("")
        self._state_path(project_id).write_text("\n".join(lines), encoding="utf-8")

    def read_state_raw(self, project_id: str) -> str:
        return _read_text(self._state_path(project_id))

    def read_roadmap_sections(self, project_id: str) -> RoadmapSections:
        text = _read_text(self._roadmap_path(project_id))
        return RoadmapSections(
            now=self._parse_section_bullets(text, "Now"),
            next=self._parse_section_bullets(text, "Next"),
            risks=self._parse_section_bullets(text, "Risks"),
        )

    def write_roadmap_sections(self, project_id: str, sections: RoadmapSections) -> None:
        payload = sections.model_dump()
        lines = [
            "# Roadmap",
            "",
            "## Now",
        ]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("now")) or ["none"])]
        lines += ["", "## Next"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("next")) or ["none"])]
        lines += ["", "## Risks"]
        lines += [f"- {item}" for item in (_ensure_list(payload.get("risks")) or ["none"])]
        lines.append("")
        self._roadmap_path(project_id).write_text("\n".join(lines), encoding="utf-8")

    def read_roadmap_raw(self, project_id: str) -> str:
        return _read_text(self._roadmap_path(project_id))

    def read_decisions(self, project_id: str) -> list[DecisionADR]:
        text = _read_text(self._decisions_path(project_id))
        blocks: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("## "):
                if current:
                    blocks.append(current)
                current = {
                    "title": line[3:].strip(),
                    "status": "Proposed",
                    "context": "",
                    "decision": "",
                    "rationale": "",
                    "consequences": [],
                    "owners": [],
                    "references": [],
                }
                continue
            if current is None:
                continue
            if line.startswith("- "):
                content = line[2:].strip()
                if ":" in content:
                    key, value = content.split(":", 1)
                    field = key.strip().lower()
                    text_value = value.strip()
                    if field == "status":
                        current["status"] = text_value
                    elif field == "context":
                        current["context"] = text_value
                    elif field == "decision":
                        current["decision"] = text_value
                    elif field == "rationale":
                        current["rationale"] = text_value
                    elif field == "consequences":
                        current["consequences"] = [token.strip() for token in text_value.split(",") if token.strip()]
                    elif field == "owners":
                        current["owners"] = [token.strip() for token in text_value.split(",") if token.strip()]
                    elif field == "references":
                        current["references"] = [token.strip() for token in text_value.split(",") if token.strip()]
        if current:
            blocks.append(current)
        return [DecisionADR.model_validate(item) for item in blocks]

    def append_decision(self, project_id: str, decision: DecisionADR) -> None:
        path = self._decisions_path(project_id)
        base = _read_text(path)
        if not base.strip():
            base = "# Decisions\n\n"
        if not base.endswith("\n"):
            base += "\n"
        item = decision.model_dump()
        lines = [
            f"## {item['title']}",
            f"- Status: {item['status']}",
        ]
        if item.get("context"):
            lines.append(f"- Context: {item['context']}")
        if item.get("decision"):
            lines.append(f"- Decision: {item['decision']}")
        if item.get("rationale"):
            lines.append(f"- Rationale: {item['rationale']}")
        if item.get("consequences"):
            lines.append(f"- Consequences: {', '.join(_ensure_list(item['consequences']))}")
        if item.get("owners"):
            lines.append(f"- Owners: {', '.join(_ensure_list(item['owners']))}")
        if item.get("references"):
            lines.append(f"- References: {', '.join(_ensure_list(item['references']))}")
        lines.append("")
        path.write_text(base + "\n".join(lines), encoding="utf-8")

    def list_agents(self, project_id: str) -> list[dict[str, Any]]:
        project_dir = self._project_dir(project_id)
        if not project_dir.exists():
            raise FileNotFoundError(f"project not found: {project_id}")
        agents_dir = self._agents_dir(project_id)
        output: list[dict[str, Any]] = []
        if not agents_dir.exists():
            return output
        for entry in sorted(agents_dir.iterdir(), key=lambda p: p.name):
            if not entry.is_dir():
                continue
            payload = _read_json(entry / "state.json", {})
            if isinstance(payload, dict):
                output.append(payload)
        return output

    def patch_agent_state(self, project_id: str, agent_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        state_path = self._agents_dir(project_id) / agent_id / "state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"agent state not found: {agent_id}")
        payload = _read_json(state_path, {})
        if not isinstance(payload, dict):
            payload = {}
        for key in ["phase", "status", "current_task", "percent", "eta_minutes"]:
            if key in patch and patch[key] is not None:
                payload[key] = patch[key]
        if "blockers" in patch and patch["blockers"] is not None:
            payload["blockers"] = _ensure_list(patch["blockers"])
        payload["heartbeat"] = _utc_now_iso()
        payload["updated_at"] = _utc_now_iso()
        _write_json(state_path, payload)
        return payload

    def load_chat(self, project_id: str, limit: int = 200) -> list[dict[str, Any]]:
        return _read_ndjson(self._chat_global_path(project_id), limit=limit)

    def append_chat(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        item = dict(payload)
        item.setdefault("message_id", f"msg_{uuid.uuid4().hex[:12]}")
        item.setdefault("timestamp", _utc_now_iso())
        item.setdefault("tags", [])
        item.setdefault("mentions", [])
        _append_ndjson(self._chat_global_path(project_id), item)
        thread_id = str(item.get("thread_id") or "").strip()
        if thread_id:
            _append_ndjson(self._project_dir(project_id) / "chat" / "threads" / f"{thread_id}.ndjson", item)
        return item

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        runs_dir = self._runs_dir(project_id)
        if not runs_dir.exists():
            return []
        rows: dict[str, dict[str, Any]] = {}
        for path in sorted(runs_dir.iterdir(), key=lambda p: p.name):
            if path.suffix not in {".json", ".md"}:
                continue
            run_id = path.stem
            rows.setdefault(run_id, {"run_id": run_id, "json_path": None, "md_path": None, "generated_at": None})
            if path.suffix == ".json":
                rows[run_id]["json_path"] = str(path)
            if path.suffix == ".md":
                rows[run_id]["md_path"] = str(path)
            rows[run_id]["generated_at"] = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        return list(rows.values())

    def get_run(self, project_id: str, run_id: str) -> dict[str, Any]:
        runs_dir = self._runs_dir(project_id)
        json_path = runs_dir / f"{run_id}.json"
        md_path = runs_dir / f"{run_id}.md"
        if not json_path.exists() and not md_path.exists():
            raise FileNotFoundError(f"run not found: {run_id}")
        return {
            "run_id": run_id,
            "json_path": str(json_path) if json_path.exists() else None,
            "md_path": str(md_path) if md_path.exists() else None,
            "json_payload": _read_json(json_path, None) if json_path.exists() else None,
            "md_text": _read_text(md_path) if md_path.exists() else None,
        }

    def _bmad_file(self, project_id: str, doc_type: str) -> Path:
        mapping = {
            "brainstorm": "BRAINSTORM.md",
            "product_brief": "PRODUCT_BRIEF.md",
            "prd": "PRD.md",
            "architecture": "ARCHITECTURE.md",
            "stories": "STORIES.md",
        }
        if doc_type not in mapping:
            raise ValueError(f"invalid doc_type: {doc_type}")
        return self._bmad_dir(project_id) / mapping[doc_type]

    def get_bmad(self, project_id: str, doc_type: str) -> dict[str, Any]:
        path = self._bmad_file(project_id, doc_type)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {doc_type.replace('_', ' ').title()}\n\n- TBD\n", encoding="utf-8")
        return {
            "project_id": project_id,
            "doc_type": doc_type,
            "content": _read_text(path),
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        }

    def put_bmad(self, project_id: str, doc_type: str, content: str) -> dict[str, Any]:
        path = self._bmad_file(project_id, doc_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = str(content).strip() + "\n"
        path.write_text(normalized, encoding="utf-8")
        return {
            "project_id": project_id,
            "doc_type": doc_type,
            "content": normalized,
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        }

    def write_run_artifacts(self, project_id: str, run_id: str, payload: dict[str, Any], markdown: str) -> dict[str, str]:
        run_token = str(run_id or "").strip()
        if not run_token:
            raise ValueError("run_id required")
        runs_dir = self._runs_dir(project_id)
        runs_dir.mkdir(parents=True, exist_ok=True)
        json_path = runs_dir / f"{run_token}.json"
        md_path = runs_dir / f"{run_token}.md"
        _write_json(json_path, payload)
        md_path.write_text(str(markdown or "").strip() + "\n", encoding="utf-8")
        return {"json_path": str(json_path), "md_path": str(md_path)}


class UserRepository:
    def __init__(self, projects_root: Path) -> None:
        self.root = Path(projects_root).expanduser() / "_api"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "users.json"
        self._ensure_default_users()

    def _ensure_default_users(self) -> None:
        if self.path.exists():
            return
        payload = {
            "owner": {
                "user_id": "owner",
                "username": "owner",
                "password_hash": hash_password("owner123!"),
                "role": "owner",
            },
            "lead": {
                "user_id": "lead",
                "username": "lead",
                "password_hash": hash_password("lead123!"),
                "role": "lead",
            },
            "viewer": {
                "user_id": "viewer",
                "username": "viewer",
                "password_hash": hash_password("viewer123!"),
                "role": "viewer",
            },
        }
        _write_json(self.path, payload)

    def all(self) -> dict[str, dict[str, Any]]:
        payload = _read_json(self.path, {})
        if not isinstance(payload, dict):
            return {}
        output: dict[str, dict[str, Any]] = {}
        for _, value in payload.items():
            if not isinstance(value, dict):
                continue
            username = str(value.get("username") or "").strip()
            if not username:
                continue
            output[username] = value
        return output

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        users = self.all()
        return users.get(str(username).strip())


class DeviceRepository:
    def __init__(self, projects_root: Path) -> None:
        self.root = Path(projects_root).expanduser() / "_api"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "devices.json"

    def _load(self) -> dict[str, Any]:
        payload = _read_json(self.path, {})
        return payload if isinstance(payload, dict) else {}

    def _save(self, payload: dict[str, Any]) -> None:
        _write_json(self.path, payload)

    def upsert(self, *, user_id: str, device_id: str, platform: str, fcm_token: str, project_ids: list[str]) -> dict[str, Any]:
        payload = self._load()
        devices = payload.get("devices")
        if not isinstance(devices, dict):
            devices = {}
        now = _utc_now_iso()
        devices[device_id] = {
            "device_id": device_id,
            "user_id": user_id,
            "platform": platform,
            "fcm_token": fcm_token,
            "project_ids": project_ids,
            "updated_at": now,
        }
        payload["devices"] = devices
        self._save(payload)
        return devices[device_id]

    def delete(self, device_id: str) -> bool:
        payload = self._load()
        devices = payload.get("devices")
        if not isinstance(devices, dict):
            return False
        if device_id not in devices:
            return False
        devices.pop(device_id, None)
        payload["devices"] = devices
        self._save(payload)
        return True
