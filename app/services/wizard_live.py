from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.codex_runner import RunnerResult, run_codex_exec


WIZARD_LIVE_VERSION = "wave19_wizard_live_v1"
DEFAULT_L1_AGENTS = ["victor", "leo", "nova", "vulgarisation"]

DEFAULT_AGENT_STATE_META: dict[str, dict[str, Any]] = {
    "clems": {
        "name": "Clems",
        "engine": "CDX",
        "platform": "codex",
        "level": 0,
        "lead_id": None,
        "role": "orchestrator",
    },
    "victor": {
        "name": "Victor",
        "engine": "CDX",
        "platform": "codex",
        "level": 1,
        "lead_id": "clems",
        "role": "backend_lead",
    },
    "leo": {
        "name": "Leo",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "ui_lead",
    },
    "nova": {
        "name": "Nova",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "creative_science_lead",
    },
    "vulgarisation": {
        "name": "Vulgarisation",
        "engine": "AG",
        "platform": "antigravity",
        "level": 1,
        "lead_id": "clems",
        "role": "vulgarisation_lead",
    },
}


@dataclass
class WizardLiveResult:
    status: str
    project_id: str
    repo_path: str
    projects_root: str
    run_id: str
    trigger: str
    session_active: bool
    output_json_path: str
    output_md_path: str
    prompt_path: str | None
    context_path: str | None
    bmad_dir: str
    runner: RunnerResult | None
    error: str | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _run_id(now: datetime | None = None) -> str:
    stamp = (now or _utc_now()).strftime("%Y-%m-%dT%H%MZ")
    return f"WIZARD_LIVE_{stamp}"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _read_text(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)] + "..."


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _read_ndjson(path: Path, limit: int = 20) -> list[dict[str, Any]]:
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


def parse_wizard_live_command(text: str) -> tuple[str | None, str]:
    raw = str(text or "").strip()
    if not raw:
        return None, ""
    match = re.match(r"^\s*#wizard-live(?:\s+(start|run|stop))?(?:\s+(.*))?\s*$", raw, flags=re.IGNORECASE)
    if not match:
        return None, ""
    command = _safe_text(match.group(1) or "run").lower()
    body = _safe_text(match.group(2))
    if command not in {"start", "run", "stop"}:
        return None, ""
    return command, body


def _session_state_path(project_dir: Path) -> Path:
    return project_dir / "runs" / "wizard_live_session.json"


def _load_session_state(project_dir: Path) -> dict[str, Any]:
    path = _session_state_path(project_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_session_state(project_dir: Path, payload: dict[str, Any]) -> Path:
    path = _session_state_path(project_dir)
    _write_json(path, payload)
    return path


def load_wizard_live_session(projects_root: Path, project_id: str) -> dict[str, Any]:
    return _load_session_state(projects_root / project_id)


def _is_ascii_text(value: Any) -> bool:
    if isinstance(value, str):
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            return False
        return True
    if isinstance(value, list):
        return all(_is_ascii_text(item) for item in value)
    if isinstance(value, dict):
        return all(_is_ascii_text(item) for item in value.values())
    return True


def _format_chat_digest(rows: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for payload in rows:
        author = _safe_text(payload.get("author")) or "unknown"
        timestamp = _safe_text(payload.get("timestamp"))
        text = _safe_text(payload.get("text"))
        if len(text) > 360:
            text = text[:357] + "..."
        prefix = f"[{timestamp}] " if timestamp else ""
        lines.append(f"- {prefix}{author}: {text}")
    return lines


def build_context_bridge(
    *,
    projects_root: Path,
    project_id: str,
    repo_path: Path,
    include_full_intake: bool,
    trigger: str,
    operator_message: str,
    l1_agents: list[str] | None = None,
) -> Path:
    project_dir = projects_root / project_id
    bmad_dir = project_dir / "BMAD"
    bmad_dir.mkdir(parents=True, exist_ok=True)
    context_path = bmad_dir / "PROJECT_CONTEXT.md"

    selected_l1 = [token for token in (l1_agents or DEFAULT_L1_AGENTS) if _safe_text(token)]
    selected_l1 = selected_l1 or list(DEFAULT_L1_AGENTS)
    memory_agents = ["clems"] + [agent_id for agent_id in selected_l1 if agent_id != "clems"]

    state_text = _read_text(project_dir / "STATE.md", 12000)
    roadmap_text = _read_text(project_dir / "ROADMAP.md", 10000)
    decisions_text = _read_text(project_dir / "DECISIONS.md", 12000)

    intake_paths = [
        ("INTAKE.md", project_dir / "INTAKE.md"),
        ("QUESTIONS.md", project_dir / "QUESTIONS.md"),
        ("PLAN.md", project_dir / "PLAN.md"),
        ("STARTUP_PACK.md", project_dir / "STARTUP_PACK.md"),
    ]
    intake_limit = 7000 if include_full_intake else 1400

    wizard_thread = _read_ndjson(project_dir / "chat" / "threads" / "wizard-live.ndjson", limit=30)
    global_rows = _read_ndjson(project_dir / "chat" / "global.ndjson", limit=20)

    lines = [
        "# Wave19 Project Context Bridge",
        "",
        f"- generated_at_utc: {_utc_now_iso()}",
        f"- project_id: {project_id}",
        f"- repo_path: {repo_path}",
        f"- trigger: {trigger}",
        f"- include_full_intake: {str(bool(include_full_intake)).lower()}",
        f"- l1_agents: {', '.join(selected_l1)}",
        "",
        "## Operator Input",
        f"- message: {_safe_text(operator_message) or '-'}",
        "",
        "## BMAD Stage Map",
        "- brainstorm -> product brief -> prd -> architecture -> stories",
        "- provide output for each stage as markdown",
        "",
        "## Cockpit Source of Truth",
        "### STATE.md",
        state_text or "- missing",
        "",
        "### ROADMAP.md",
        roadmap_text or "- missing",
        "",
        "### DECISIONS.md",
        decisions_text or "- missing",
        "",
        "## Intake and Startup Artifacts",
    ]

    for label, path in intake_paths:
        lines.append(f"### {label}")
        excerpt = _read_text(path, intake_limit)
        lines.append(excerpt or "- missing")
        lines.append("")

    lines += [
        "## Agent Memories",
    ]
    for agent_id in memory_agents:
        memory_path = project_dir / "agents" / agent_id / "memory.md"
        lines.append(f"### {agent_id}")
        lines.append(_read_text(memory_path, 5500) or "- missing")
        lines.append("")

    lines += [
        "## Chat Digest (wizard-live thread)",
    ]
    lines.extend(_format_chat_digest(wizard_thread) or ["- none"])
    lines += [
        "",
        "## Chat Digest (global recent)",
    ]
    lines.extend(_format_chat_digest(global_rows) or ["- none"])
    lines.append("")

    _write_text(context_path, "\n".join(lines).strip() + "\n")
    return context_path


def _wizard_prompt(
    *,
    project_id: str,
    repo_path: Path,
    trigger: str,
    operator_message: str,
    l1_agents: list[str],
    context_text: str,
) -> str:
    root_dir = Path(__file__).resolve().parents[2]
    persona_ids = ["clems"] + [agent_id for agent_id in l1_agents if agent_id != "clems"]
    personas: list[str] = []
    for agent_id in persona_ids:
        persona_path = root_dir / "agents" / f"{agent_id}.md"
        if persona_path.exists():
            personas.append(f"## Persona - {agent_id}\n{_read_text(persona_path, 12000)}")

    l1_list = ", ".join(l1_agents)
    expected_count = len(DEFAULT_L1_AGENTS)
    return "\n".join(
        [
            "[Cockpit Wave19 Wizard Live]",
            f"PROJECT LOCK: {project_id}",
            "ASCII ONLY. Keep messages short and actionable.",
            "Strict output: JSON only, must match provided schema.",
            "",
            f"Project: {project_id}",
            f"Repo path (read-only): {repo_path}",
            f"Trigger: {trigger}",
            f"L1 agents (exact): {l1_list}",
            f"Operator message: {_safe_text(operator_message) or '-'}",
            "",
            "Required JSON shape:",
            f"- agent_messages must contain EXACTLY {expected_count} entries: {', '.join(DEFAULT_L1_AGENTS)}.",
            "- Include clems_summary with synthesis and decision-ready next actions.",
            "- Include bmad with brainstorm, product_brief, prd, architecture, stories markdown.",
            "- Include state_sections, roadmap_sections, decisions_adrs.",
            "",
            "Nova deep research requirement (mandatory):",
            "- Nova text must include owner, next_action, evidence_path, decision_tag (adopt/defer/reject).",
            "",
            "Execution constraints:",
            "- Do not propose writing code in target repo.",
            "- Read-only takeover planning and operation only.",
            "- Respect L0/L1 hierarchy and lead-first execution.",
            "",
            "Context bridge:",
            context_text,
            "",
            "Personas:",
            "\n\n".join(personas),
        ]
    ).strip()


def _validate_output(payload: dict[str, Any]) -> tuple[bool, str]:
    required = [
        "wizard_version",
        "generated_at_utc",
        "project_id",
        "repo_path",
        "trigger",
        "agent_messages",
        "clems_summary",
        "bmad",
        "state_sections",
        "roadmap_sections",
        "decisions_adrs",
    ]
    for key in required:
        if key not in payload:
            return False, f"missing_field:{key}"

    agent_messages = payload.get("agent_messages")
    if not isinstance(agent_messages, list) or len(agent_messages) != len(DEFAULT_L1_AGENTS):
        return False, "invalid_agent_messages_count"
    seen_ids: list[str] = []
    for item in agent_messages:
        if not isinstance(item, dict):
            return False, "invalid_agent_message"
        agent_id = _safe_text(item.get("agent_id")).lower()
        if not agent_id:
            return False, "missing_agent_id"
        seen_ids.append(agent_id)
        if not isinstance(item.get("text"), str):
            return False, f"invalid_agent_text:{agent_id}"
        for field in ["now", "next", "blockers"]:
            if not isinstance(item.get(field), list):
                return False, f"invalid_agent_field:{agent_id}:{field}"
        state_update = item.get("state_update")
        if not isinstance(state_update, dict):
            return False, f"invalid_state_update:{agent_id}"
        for field in ["phase", "status", "current_task"]:
            if not _safe_text(state_update.get(field)):
                return False, f"missing_state_update_field:{agent_id}:{field}"

    if set(seen_ids) != set(DEFAULT_L1_AGENTS):
        return False, "invalid_agent_messages_l1"
    if not _is_ascii_text(agent_messages):
        return False, "non_ascii_agent_messages"

    nova_message = next((item for item in agent_messages if _safe_text(item.get("agent_id")).lower() == "nova"), {})
    nova_text = _safe_text(nova_message.get("text")).lower()
    for marker in ["owner", "next_action", "evidence_path", "decision_tag"]:
        if marker not in nova_text:
            return False, f"nova_deep_research_missing:{marker}"

    clems_summary = payload.get("clems_summary")
    if not isinstance(clems_summary, dict):
        return False, "invalid_clems_summary"
    if not _safe_text(clems_summary.get("text")):
        return False, "invalid_clems_summary_text"
    for field in ["now", "next", "blockers"]:
        if not isinstance(clems_summary.get(field), list):
            return False, f"invalid_clems_summary_field:{field}"
    clems_state = clems_summary.get("state_update")
    if not isinstance(clems_state, dict):
        return False, "invalid_clems_state_update"
    for field in ["phase", "status", "current_task"]:
        if not _safe_text(clems_state.get(field)):
            return False, f"missing_clems_state_update_field:{field}"
    if not _is_ascii_text(clems_summary):
        return False, "non_ascii_clems_summary"

    bmad = payload.get("bmad")
    if not isinstance(bmad, dict):
        return False, "invalid_bmad"
    for key in ["brainstorm_md", "product_brief_md", "prd_md", "architecture_md", "stories_md"]:
        if not isinstance(bmad.get(key), str):
            return False, f"missing_bmad:{key}"
    if not _is_ascii_text(bmad):
        return False, "non_ascii_bmad"

    state_sections = payload.get("state_sections")
    if not isinstance(state_sections, dict):
        return False, "invalid_state_sections"
    for key in ["phase", "objective", "now", "next", "in_progress", "blockers", "risks", "links"]:
        if key not in state_sections:
            return False, f"missing_state_sections:{key}"
    if not _is_ascii_text(state_sections):
        return False, "non_ascii_state_sections"

    roadmap_sections = payload.get("roadmap_sections")
    if not isinstance(roadmap_sections, dict):
        return False, "invalid_roadmap_sections"
    for key in ["now", "next", "risks"]:
        if not isinstance(roadmap_sections.get(key), list):
            return False, f"invalid_roadmap_sections:{key}"
    if not _is_ascii_text(roadmap_sections):
        return False, "non_ascii_roadmap_sections"

    decisions_adrs = payload.get("decisions_adrs")
    if not isinstance(decisions_adrs, list):
        return False, "invalid_decisions_adrs"
    if not _is_ascii_text(decisions_adrs):
        return False, "non_ascii_decisions"

    return True, ""


def _state_md_from_sections(sections: dict[str, Any]) -> str:
    def _as_list(key: str) -> list[str]:
        raw = sections.get(key)
        if isinstance(raw, list):
            return [_safe_text(item) for item in raw if _safe_text(item)]
        if isinstance(raw, str) and raw.strip():
            return [_safe_text(raw)]
        return []

    phase = _safe_text(sections.get("phase")) or "Plan"
    objective = _safe_text(sections.get("objective")) or "TBD"
    now_items = _as_list("now")
    next_items = _as_list("next")
    in_progress_items = _as_list("in_progress")
    blockers = _as_list("blockers")
    risks = _as_list("risks")
    links = _as_list("links")

    lines = [
        "# State",
        "",
        "## Phase",
        f"- {phase}",
        "",
        "## Objective",
        f"- {objective}",
        "",
        "## Now",
    ]
    lines += [f"- {item}" for item in (now_items or ["none"])]
    lines += ["", "## Next"]
    lines += [f"- {item}" for item in (next_items or ["none"])]
    lines += ["", "## In Progress"]
    lines += [f"- {item}" for item in (in_progress_items or ["none"])]
    lines += ["", "## Blockers"]
    lines += [f"- {item}" for item in (blockers or ["none"])]
    lines += ["", "## Risks"]
    lines += [f"- {item}" for item in (risks or ["none"])]
    lines += ["", "## Links"]
    lines += [f"- {item}" for item in (links or ["none"])]
    lines.append("")
    return "\n".join(lines)


def _roadmap_md_from_sections(sections: dict[str, Any]) -> str:
    def _as_list(key: str) -> list[str]:
        raw = sections.get(key)
        if isinstance(raw, list):
            return [_safe_text(item) for item in raw if _safe_text(item)]
        if isinstance(raw, str) and raw.strip():
            return [_safe_text(raw)]
        return []

    now_items = _as_list("now")
    next_items = _as_list("next")
    risks = _as_list("risks")
    lines = [
        "# Roadmap",
        "",
        "## Now",
    ]
    lines += [f"- {item}" for item in (now_items or ["none"])]
    lines += ["", "## Next"]
    lines += [f"- {item}" for item in (next_items or ["none"])]
    lines += ["", "## Risks"]
    lines += [f"- {item}" for item in (risks or ["none"])]
    lines.append("")
    return "\n".join(lines)


def _append_decisions(decisions_path: Path, decisions: list[dict[str, Any]]) -> None:
    if not decisions:
        return
    lines: list[str] = []
    for item in decisions:
        if not isinstance(item, dict):
            continue
        title = _safe_text(item.get("title"))
        if not title:
            continue
        status = _safe_text(item.get("status")) or "Proposed"
        context = _safe_text(item.get("context"))
        decision = _safe_text(item.get("decision"))
        rationale = _safe_text(item.get("rationale"))
        consequences = item.get("consequences") if isinstance(item.get("consequences"), list) else []
        owners = item.get("owners") if isinstance(item.get("owners"), list) else []
        references = item.get("references") if isinstance(item.get("references"), list) else []

        lines.append(f"## {title}")
        lines.append(f"- Status: {status}")
        if context:
            lines.append(f"- Context: {context}")
        if decision:
            lines.append(f"- Decision: {decision}")
        if rationale:
            lines.append(f"- Rationale: {rationale}")
        if consequences:
            lines.append(f"- Consequences: {', '.join(_safe_text(item) for item in consequences if _safe_text(item))}")
        if owners:
            lines.append(f"- Owners: {', '.join(_safe_text(item) for item in owners if _safe_text(item))}")
        if references:
            lines.append(f"- References: {', '.join(_safe_text(item) for item in references if _safe_text(item))}")
        lines.append("")

    if not lines:
        return
    if decisions_path.exists():
        base = _read_text(decisions_path, 300000)
        if not base.endswith("\n"):
            base += "\n"
    else:
        base = "# Decisions\n\n"
    _write_text(decisions_path, base + "\n".join(lines))


def _append_chat(
    project_dir: Path,
    *,
    author: str,
    text: str,
    event: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "author": author,
        "text": text,
        "tags": ["wizard-live"],
        "mentions": [],
    }
    if event:
        payload["event"] = event
    _append_ndjson(project_dir / "chat" / "global.ndjson", payload)
    _append_ndjson(project_dir / "chat" / "threads" / "wizard-live.ndjson", payload)


def _ensure_agent_state(project_dir: Path, agent_id: str) -> Path:
    state_path = project_dir / "agents" / agent_id / "state.json"
    if state_path.exists():
        return state_path
    defaults = dict(DEFAULT_AGENT_STATE_META.get(agent_id, {}))
    payload = {
        "agent_id": agent_id,
        "name": _safe_text(defaults.get("name")) or agent_id.title(),
        "engine": _safe_text(defaults.get("engine")) or "CDX",
        "platform": _safe_text(defaults.get("platform")) or "codex",
        "level": int(defaults.get("level", 2)),
        "lead_id": defaults.get("lead_id", "clems"),
        "role": _safe_text(defaults.get("role")) or "specialist",
        "skills": [],
        "phase": "Plan",
        "percent": 0,
        "eta_minutes": None,
        "heartbeat": _utc_now_iso(),
        "status": "idle",
        "blockers": [],
        "current_task": "",
        "updated_at": _utc_now_iso(),
    }
    _write_json(state_path, payload)
    return state_path


def _normalize_blockers(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    if isinstance(value, str) and value.strip():
        return [_safe_text(value)]
    return []


def _apply_agent_state_update(project_dir: Path, agent_id: str, state_update: dict[str, Any]) -> None:
    state_path = _ensure_agent_state(project_dir, agent_id)
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    payload["phase"] = _safe_text(state_update.get("phase")) or payload.get("phase") or "Plan"
    payload["status"] = _safe_text(state_update.get("status")) or payload.get("status") or "planning"
    payload["current_task"] = _safe_text(state_update.get("current_task")) or payload.get("current_task") or ""
    blockers = _normalize_blockers(state_update.get("blockers"))
    if blockers:
        payload["blockers"] = blockers

    if "percent" in state_update:
        try:
            payload["percent"] = max(0, min(int(state_update.get("percent") or 0), 100))
        except (TypeError, ValueError):
            pass
    if "eta_minutes" in state_update:
        try:
            eta = state_update.get("eta_minutes")
            payload["eta_minutes"] = None if eta is None else int(eta)
        except (TypeError, ValueError):
            payload["eta_minutes"] = None

    payload["heartbeat"] = _utc_now_iso()
    payload["updated_at"] = _utc_now_iso()
    _write_json(state_path, payload)


def _write_bmad(project_dir: Path, bmad: dict[str, Any]) -> Path:
    bmad_dir = project_dir / "BMAD"
    bmad_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "BRAINSTORM.md": _safe_text(bmad.get("brainstorm_md")),
        "PRODUCT_BRIEF.md": _safe_text(bmad.get("product_brief_md")),
        "PRD.md": _safe_text(bmad.get("prd_md")),
        "ARCHITECTURE.md": _safe_text(bmad.get("architecture_md")),
        "STORIES.md": _safe_text(bmad.get("stories_md")),
    }
    for filename, content in mapping.items():
        normalized = content or f"# {filename.replace('.md', '').replace('_', ' ')}\n\n- TBD\n"
        _write_text(bmad_dir / filename, normalized.strip() + "\n")
    return bmad_dir


def apply_wizard_live_output(
    *,
    projects_root: Path,
    project_id: str,
    output_payload: dict[str, Any],
    run_id: str,
    repo_path: Path,
    trigger: str,
    operator_message: str,
    prompt_path: Path | None,
    context_path: Path | None,
    runner: RunnerResult | None,
    session_active: bool,
) -> WizardLiveResult:
    project_dir = projects_root / project_id
    runs_dir = project_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_json_path = runs_dir / f"{run_id}.json"
    output_md_path = runs_dir / f"{run_id}.md"

    is_valid, reason = _validate_output(output_payload)
    if not is_valid:
        raise ValueError(f"wizard_live_output_invalid:{reason}")

    _write_json(output_json_path, output_payload)

    bmad = output_payload.get("bmad") if isinstance(output_payload.get("bmad"), dict) else {}
    bmad_dir = _write_bmad(project_dir, bmad)

    state_sections = output_payload.get("state_sections") if isinstance(output_payload.get("state_sections"), dict) else {}
    roadmap_sections = (
        output_payload.get("roadmap_sections") if isinstance(output_payload.get("roadmap_sections"), dict) else {}
    )
    _write_text(project_dir / "STATE.md", _state_md_from_sections(state_sections))
    _write_text(project_dir / "ROADMAP.md", _roadmap_md_from_sections(roadmap_sections))

    decisions = output_payload.get("decisions_adrs") if isinstance(output_payload.get("decisions_adrs"), list) else []
    _append_decisions(project_dir / "DECISIONS.md", decisions)

    agent_messages = output_payload.get("agent_messages") if isinstance(output_payload.get("agent_messages"), list) else []
    ordered = {agent_id: None for agent_id in DEFAULT_L1_AGENTS}
    for item in agent_messages:
        if isinstance(item, dict):
            key = _safe_text(item.get("agent_id")).lower()
            if key in ordered:
                ordered[key] = item

    for agent_id in DEFAULT_L1_AGENTS:
        item = ordered.get(agent_id)
        if not isinstance(item, dict):
            continue
        text = _safe_text(item.get("text"))
        state_update = item.get("state_update") if isinstance(item.get("state_update"), dict) else {}
        if text:
            _append_chat(project_dir, author=agent_id, text=text, event="wizard_live_agent")
        if state_update:
            _apply_agent_state_update(project_dir, agent_id, state_update)

    clems_summary = output_payload.get("clems_summary") if isinstance(output_payload.get("clems_summary"), dict) else {}
    clems_text = _safe_text(clems_summary.get("text"))
    if clems_text:
        _append_chat(project_dir, author="clems", text=clems_text, event="wizard_live_summary")
    clems_state_update = (
        clems_summary.get("state_update") if isinstance(clems_summary.get("state_update"), dict) else {}
    )
    if clems_state_update:
        _apply_agent_state_update(project_dir, "clems", clems_state_update)

    summary_lines = [
        f"Wizard Live complete: {run_id}",
        f"- project_id={project_id}",
        f"- trigger={trigger}",
        f"- repo_path={repo_path}",
        f"- output_json={output_json_path}",
        f"- bmad_dir={bmad_dir}",
    ]
    if operator_message:
        summary_lines.append(f"- operator_message={operator_message}")
    if prompt_path is not None:
        summary_lines.append(f"- prompt_path={prompt_path}")
    if context_path is not None:
        summary_lines.append(f"- context_path={context_path}")
    if runner is not None:
        summary_lines.append(f"- runner_status={runner.status} success={runner.success}")
    _append_chat(project_dir, author="system", text="\n".join(summary_lines), event="wizard_live_complete")

    command = (
        f"scripts/wizard_live.py start --project-id {project_id} --repo-path {repo_path} "
        "--data-dir app --trigger chat"
    )
    md_lines = [
        f"# Wizard Live Run - {run_id}",
        "",
        f"- timestamp_utc: {_utc_now_iso()}",
        f"- project_id: {project_id}",
        f"- projects_root: {projects_root}",
        f"- repo_path: {repo_path}",
        f"- trigger: {trigger}",
        f"- session_active: {str(bool(session_active)).lower()}",
        f"- command: {command}",
        "",
        "## Operator Input",
        f"- message: {operator_message or '-'}",
        "",
        "## Outputs",
        f"- {output_json_path}",
        f"- {bmad_dir}",
        f"- {project_dir / 'STATE.md'}",
        f"- {project_dir / 'ROADMAP.md'}",
        f"- {project_dir / 'DECISIONS.md'}",
        "",
        "## Runner",
    ]
    if runner is None:
        md_lines.append("- runner: none")
    else:
        md_lines += [
            f"- runner: {runner.runner}",
            f"- status: {runner.status}",
            f"- success: {runner.success}",
            f"- error: {runner.error or ''}",
        ]
    if prompt_path is not None:
        md_lines += ["", "## Prompt", f"- {prompt_path}"]
    if context_path is not None:
        md_lines += ["", "## Context", f"- {context_path}"]
    md_lines.append("")
    _write_text(output_md_path, "\n".join(md_lines))

    return WizardLiveResult(
        status="ok",
        project_id=project_id,
        repo_path=str(repo_path),
        projects_root=str(projects_root),
        run_id=run_id,
        trigger=trigger,
        session_active=bool(session_active),
        output_json_path=str(output_json_path),
        output_md_path=str(output_md_path),
        prompt_path=str(prompt_path) if prompt_path is not None else None,
        context_path=str(context_path) if context_path is not None else None,
        bmad_dir=str(bmad_dir),
        runner=runner,
        error=None,
    )


def _write_failed_run_log(
    *,
    output_md_path: Path,
    run_id: str,
    project_id: str,
    projects_root: Path,
    repo_path: Path,
    trigger: str,
    operator_message: str,
    error: str,
    prompt_path: Path | None,
    context_path: Path | None,
    runner: RunnerResult | None,
) -> None:
    lines = [
        f"# Wizard Live Run - {run_id}",
        "",
        f"- timestamp_utc: {_utc_now_iso()}",
        f"- project_id: {project_id}",
        f"- projects_root: {projects_root}",
        f"- repo_path: {repo_path}",
        f"- trigger: {trigger}",
        f"- status: failed",
        "",
        "## Operator Input",
        f"- message: {operator_message or '-'}",
        "",
        "## Error",
        f"- {error}",
        "",
        "## Runner",
    ]
    if runner is None:
        lines.append("- runner: none")
    else:
        lines += [
            f"- runner: {runner.runner}",
            f"- status: {runner.status}",
            f"- success: {runner.success}",
            f"- error: {runner.error or ''}",
        ]
    if prompt_path is not None:
        lines += ["", "## Prompt", f"- {prompt_path}"]
    if context_path is not None:
        lines += ["", "## Context", f"- {context_path}"]
    lines.append("")
    _write_text(output_md_path, "\n".join(lines))


def run_wizard_live_turn(
    *,
    projects_root: Path,
    project_id: str,
    repo_path: Path,
    trigger: str,
    operator_message: str = "",
    include_full_intake: bool = False,
    timeout_s: int = 240,
    l1_agents: list[str] | None = None,
    session_active: bool = True,
) -> WizardLiveResult:
    now = _utc_now()
    run_id = _run_id(now)
    project_dir = projects_root / project_id
    runs_dir = project_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    repo_path = Path(repo_path).expanduser().resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"repo_path_not_found:{repo_path}")
    if not repo_path.is_dir():
        raise NotADirectoryError(f"repo_path_not_dir:{repo_path}")

    selected_l1 = [token for token in (l1_agents or DEFAULT_L1_AGENTS) if _safe_text(token)]
    selected_l1 = selected_l1 or list(DEFAULT_L1_AGENTS)

    context_path = build_context_bridge(
        projects_root=projects_root,
        project_id=project_id,
        repo_path=repo_path,
        include_full_intake=bool(include_full_intake),
        trigger=trigger,
        operator_message=operator_message,
        l1_agents=selected_l1,
    )
    context_text = _read_text(context_path, 110000)

    prompt = _wizard_prompt(
        project_id=project_id,
        repo_path=repo_path,
        trigger=trigger,
        operator_message=operator_message,
        l1_agents=selected_l1,
        context_text=context_text,
    )
    prompt_path = runs_dir / f"{run_id}_prompt.txt"
    _write_text(prompt_path, prompt + "\n")

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "wizard_live_output.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parents[2] / "app" / "schemas" / "wizard_live_output.schema.json"

    runner_result = run_codex_exec(
        prompt,
        cwd=repo_path,
        timeout_s=timeout_s,
        sandbox_mode="read-only",
        approval_policy="never",
        output_schema_path=schema_path if schema_path.exists() else None,
        output_last_message_path=runs_dir / f"{run_id}_codex_output.json",
        ephemeral=True,
    )

    output_md_path = runs_dir / f"{run_id}.md"
    if not runner_result.success or not runner_result.output_text.strip():
        error = runner_result.error or "wizard_live_exec_failed"
        _append_chat(
            project_dir,
            author="system",
            text=f"Wizard Live failed: {error}. Prompt: {prompt_path}",
            event="wizard_live_failed",
        )
        _write_failed_run_log(
            output_md_path=output_md_path,
            run_id=run_id,
            project_id=project_id,
            projects_root=projects_root,
            repo_path=repo_path,
            trigger=trigger,
            operator_message=operator_message,
            error=error,
            prompt_path=prompt_path,
            context_path=context_path,
            runner=runner_result,
        )
        return WizardLiveResult(
            status="failed",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id=run_id,
            trigger=trigger,
            session_active=bool(session_active),
            output_json_path="",
            output_md_path=str(output_md_path),
            prompt_path=str(prompt_path),
            context_path=str(context_path),
            bmad_dir=str(project_dir / "BMAD"),
            runner=runner_result,
            error=error,
        )

    try:
        payload = json.loads(runner_result.output_text)
    except json.JSONDecodeError as exc:
        error = f"invalid_json:{exc}"
        _append_chat(
            project_dir,
            author="system",
            text=f"Wizard Live invalid JSON: {error}. Prompt: {prompt_path}",
            event="wizard_live_failed",
        )
        _write_failed_run_log(
            output_md_path=output_md_path,
            run_id=run_id,
            project_id=project_id,
            projects_root=projects_root,
            repo_path=repo_path,
            trigger=trigger,
            operator_message=operator_message,
            error=error,
            prompt_path=prompt_path,
            context_path=context_path,
            runner=runner_result,
        )
        return WizardLiveResult(
            status="failed",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id=run_id,
            trigger=trigger,
            session_active=bool(session_active),
            output_json_path="",
            output_md_path=str(output_md_path),
            prompt_path=str(prompt_path),
            context_path=str(context_path),
            bmad_dir=str(project_dir / "BMAD"),
            runner=runner_result,
            error=error,
        )

    if not isinstance(payload, dict):
        raise ValueError("wizard_live_output_invalid:root_not_object")

    payload.setdefault("wizard_version", WIZARD_LIVE_VERSION)
    payload.setdefault("generated_at_utc", _utc_now_iso())
    payload.setdefault("project_id", project_id)
    payload.setdefault("repo_path", str(repo_path))
    payload.setdefault("trigger", trigger)

    return apply_wizard_live_output(
        projects_root=projects_root,
        project_id=project_id,
        output_payload=payload,
        run_id=run_id,
        repo_path=repo_path,
        trigger=trigger,
        operator_message=operator_message,
        prompt_path=prompt_path,
        context_path=context_path,
        runner=runner_result,
        session_active=bool(session_active),
    )


def start_wizard_live_session(
    *,
    projects_root: Path,
    project_id: str,
    repo_path: Path,
    operator_message: str = "",
    trigger: str = "wizard_live_start",
    timeout_s: int = 240,
    run_initial: bool = True,
    l1_agents: list[str] | None = None,
) -> WizardLiveResult:
    project_dir = projects_root / project_id
    repo_path = Path(repo_path).expanduser().resolve()
    session_payload = _load_session_state(project_dir)
    session_payload.update(
        {
            "active": True,
            "project_id": project_id,
            "repo_path": str(repo_path),
            "status": "active",
            "last_error": "",
            "updated_at": _utc_now_iso(),
        }
    )
    if not _safe_text(session_payload.get("started_at")):
        session_payload["started_at"] = _utc_now_iso()
    _save_session_state(project_dir, session_payload)

    _append_chat(
        project_dir,
        author="system",
        text=f"Wizard Live session started (trigger={trigger}).",
        event="wizard_live_session_started",
    )

    if not run_initial:
        return WizardLiveResult(
            status="started",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id="",
            trigger=trigger,
            session_active=True,
            output_json_path="",
            output_md_path="",
            prompt_path=None,
            context_path=None,
            bmad_dir=str(project_dir / "BMAD"),
            runner=None,
            error=None,
        )

    result = run_wizard_live_turn(
        projects_root=projects_root,
        project_id=project_id,
        repo_path=repo_path,
        trigger=trigger,
        operator_message=operator_message,
        include_full_intake=True,
        timeout_s=timeout_s,
        l1_agents=l1_agents,
        session_active=True,
    )

    updated = _load_session_state(project_dir)
    updated["active"] = True
    updated["repo_path"] = str(repo_path)
    updated["updated_at"] = _utc_now_iso()
    if result.status == "ok":
        updated["status"] = "active"
        updated["last_run_id"] = result.run_id
        updated["last_error"] = ""
        _save_session_state(project_dir, updated)
        return result

    updated["status"] = "degraded"
    updated["last_error"] = result.error or "wizard_live_start_failed"
    _save_session_state(project_dir, updated)
    result.status = "degraded"
    return result


def stop_wizard_live_session(
    *,
    projects_root: Path,
    project_id: str,
    trigger: str = "wizard_live_stop",
    reason: str = "",
) -> WizardLiveResult:
    project_dir = projects_root / project_id
    session_payload = _load_session_state(project_dir)
    repo_path = _safe_text(session_payload.get("repo_path"))
    session_payload["active"] = False
    session_payload["status"] = "stopped"
    session_payload["updated_at"] = _utc_now_iso()
    if reason:
        session_payload["last_reason"] = reason
    _save_session_state(project_dir, session_payload)

    msg = "Wizard Live session stopped."
    if reason:
        msg += f" reason={reason}"
    _append_chat(project_dir, author="system", text=msg, event="wizard_live_session_stopped")

    return WizardLiveResult(
        status="stopped",
        project_id=project_id,
        repo_path=repo_path,
        projects_root=str(projects_root),
        run_id="",
        trigger=trigger,
        session_active=False,
        output_json_path="",
        output_md_path="",
        prompt_path=None,
        context_path=None,
        bmad_dir=str(project_dir / "BMAD"),
        runner=None,
        error=None,
    )
