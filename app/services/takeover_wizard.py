from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.agent_registry import load_agent_registry
from app.services.brain_manager import BrainManager
from app.services.openrouter_runner import RunnerResult, run_openrouter_exec
from app.services.project_intake import scan_repo


WIZARD_VERSION = "wave18_takeover_wizard_v1"
DEFAULT_L1_ORDER = ["victor", "leo", "nova"]


@dataclass(frozen=True)
class TakeoverWizardResult:
    status: str
    project_id: str
    repo_path: str
    projects_root: str
    run_id: str
    output_json_path: str
    output_md_path: str
    prompt_path: str | None
    bmad_dir: str
    runner: RunnerResult | None
    error: str | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _run_id(now: datetime | None = None) -> str:
    stamp = (now or _utc_now()).strftime("%Y-%m-%dT%H%MZ")
    return f"TAKEOVER_WIZARD_{stamp}"


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


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _list_l1_agents(project_id: str, projects_root: Path, override: list[str] | None) -> list[str]:
    if override is not None:
        return [token for token in (str(item).strip() for item in override) if token]

    registry = load_agent_registry(project_id, projects_root)
    l1 = [agent_id for agent_id, meta in registry.items() if int(getattr(meta, "level", 2) or 2) == 1]
    ordered: list[str] = []
    for pref in DEFAULT_L1_ORDER:
        if pref in l1 and pref not in ordered:
            ordered.append(pref)
    for agent_id in sorted(l1):
        if agent_id not in ordered:
            ordered.append(agent_id)
    return ordered or list(DEFAULT_L1_ORDER)


def _validate_output(payload: dict[str, Any]) -> tuple[bool, str]:
    required = [
        "wizard_version",
        "generated_at_utc",
        "project_id",
        "repo_path",
        "agent_messages",
        "bmad",
        "roadmap_sections",
        "decisions_adrs",
    ]
    for key in required:
        if key not in payload:
            return False, f"missing_field:{key}"

    agent_messages = payload.get("agent_messages")
    if not isinstance(agent_messages, list) or not agent_messages:
        return False, "invalid_agent_messages"

    bmad = payload.get("bmad")
    if not isinstance(bmad, dict):
        return False, "invalid_bmad"
    for key in ["product_brief_md", "prd_md", "architecture_md", "stories_md"]:
        if key not in bmad or not isinstance(bmad.get(key), str):
            return False, f"missing_bmad:{key}"

    state_md = payload.get("state_md")
    state_sections = payload.get("state_sections")
    if not (isinstance(state_md, str) and state_md.strip()) and not isinstance(state_sections, dict):
        return False, "missing_state"

    roadmap_sections = payload.get("roadmap_sections")
    if not isinstance(roadmap_sections, dict):
        return False, "invalid_roadmap_sections"
    for key in ["now", "next", "risks"]:
        raw = roadmap_sections.get(key)
        if raw is None:
            continue
        if not isinstance(raw, list):
            return False, f"invalid_roadmap_sections:{key}"

    decisions_adrs = payload.get("decisions_adrs")
    if not isinstance(decisions_adrs, list):
        return False, "invalid_decisions_adrs"

    return True, ""


def _state_md_from_sections(sections: dict[str, Any]) -> str:
    phase = _safe_text(sections.get("phase"))
    objective = _safe_text(sections.get("objective"))

    def _as_list(key: str) -> list[str]:
        raw = sections.get(key)
        if isinstance(raw, list):
            return [_safe_text(item) for item in raw if _safe_text(item)]
        if isinstance(raw, str) and raw.strip():
            return [_safe_text(raw)]
        return []

    now_items = _as_list("now")
    next_items = _as_list("next")
    in_progress = _as_list("in_progress")
    blockers = _as_list("blockers")
    risks = _as_list("risks")
    links = _as_list("links")

    lines = ["# State", "", "## Phase", f"- {phase or 'Plan'}", "", "## Objective", f"- {objective or 'TBD'}", ""]
    lines += ["## Now"]
    lines += [f"- {item}" for item in (now_items or ["-"])]
    if not now_items:
        lines[-1] = "- -"
    lines += ["", "## Next"]
    lines += [f"- {item}" for item in (next_items or ["-"])]
    if not next_items:
        lines[-1] = "- -"
    lines += ["", "## In Progress"]
    lines += [f"- {item}" for item in (in_progress or ["-"])]
    if not in_progress:
        lines[-1] = "- -"
    lines += ["", "## Blockers"]
    lines += [f"- {item}" for item in (blockers or ["-"])]
    if not blockers:
        lines[-1] = "- -"
    lines += ["", "## Risks"]
    lines += [f"- {item}" for item in (risks or ["-"])]
    if not risks:
        lines[-1] = "- -"
    lines += ["", "## Links"]
    lines += [f"- {item}" for item in (links or ["-"])]
    if not links:
        lines[-1] = "- -"
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

    lines = ["# Roadmap", "", "## Now"]
    lines += [f"- {item}" for item in (now_items or ["-"])]
    if not now_items:
        lines[-1] = "- -"
    lines += ["", "## Next"]
    lines += [f"- {item}" for item in (next_items or ["-"])]
    if not next_items:
        lines[-1] = "- -"
    lines += ["", "## Risks"]
    lines += [f"- {item}" for item in (risks or ["-"])]
    if not risks:
        lines[-1] = "- -"
    lines.append("")
    return "\n".join(lines)


def _append_decisions(decisions_path: Path, decisions: list[dict[str, Any]]) -> None:
    if not decisions:
        return

    lines = []
    for item in decisions:
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
            lines.append(f"- Consequences: {', '.join(_safe_text(c) for c in consequences if _safe_text(c))}")
        if owners:
            lines.append(f"- Owners: {', '.join(_safe_text(o) for o in owners if _safe_text(o))}")
        if references:
            lines.append(f"- References: {', '.join(_safe_text(r) for r in references if _safe_text(r))}")
        lines.append("")

    if not lines:
        return

    if decisions_path.exists():
        base = _read_text(decisions_path, max_chars=200000)
        if not base.strip().endswith("\n"):
            base = base + "\n"
    else:
        base = "# Decisions\n\n"

    content = base + "\n".join(lines)
    _write_text(decisions_path, content)


def _ensure_agent_state(project_dir: Path, agent_id: str) -> Path:
    state_path = project_dir / "agents" / agent_id / "state.json"
    if state_path.exists():
        return state_path
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "agent_id": agent_id,
        "name": agent_id.title(),
        "engine": "OR",
        "platform": "openrouter",
        "level": 2,
        "lead_id": "clems",
        "role": "specialist",
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
    if "percent" in state_update:
        try:
            payload["percent"] = int(state_update.get("percent") or 0)
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


def _wizard_prompt(
    *,
    project_id: str,
    repo_path: Path,
    l1_agents: list[str],
    intake: dict[str, Any] | None,
    plan: dict[str, Any] | None,
    questions: list[str] | None,
) -> str:
    repo = str(repo_path)
    l1 = ", ".join(l1_agents)
    intake_payload = intake if isinstance(intake, dict) else {}
    plan_payload = plan if isinstance(plan, dict) else {}
    questions_list = questions if isinstance(questions, list) else []

    # Keep prompt deterministic + ASCII-only guidance.
    personas: list[str] = []
    root_dir = Path(__file__).resolve().parents[2]
    for agent_id in l1_agents:
        persona_path = root_dir / "agents" / f"{agent_id}.md"
        if persona_path.exists():
            personas.append(f"## Persona - {agent_id}\n{_read_text(persona_path, 12000)}\n")

    intake_json = json.dumps(
        {
            "intake": intake_payload,
            "plan": plan_payload,
            "questions": questions_list[:20],
        },
        ensure_ascii=True,
        sort_keys=True,
    )

    return "\n".join(
        [
            "[Cockpit Takeover Wizard]",
            f"PROJECT LOCK: {project_id}",
            "ASCII ONLY. Be short and actionable.",
            "",
            "You must output STRICT JSON that matches the provided JSON schema.",
            "Do not output markdown outside JSON fields.",
            "",
            f"Project: {project_id}",
            f"Repo path (read-only): {repo}",
            f"L1 agents: {l1}",
            "",
            "Mission:",
            "- Produce BMAD artifacts as markdown strings: product brief, PRD, architecture, stories.",
            "- Produce a roundtable for each L1 agent with Now/Next/Blockers (2-3 bullets each).",
            "- Update a draft STATE (phase/objective/now/next/blockers/risks/links).",
            "- Update a draft ROADMAP (now/next/risks).",
            "- Provide decisions_adrs as a list (can be empty).",
            "",
            "Nova requirement (mandatory):",
            "- Include at least 1 deep research item in Nova output with: owner, next action, evidence path, decision tag (adopt/defer/reject).",
            "",
            "Input (deterministic intake JSON):",
            intake_json,
            "",
            "Personas (only for the L1 agents):",
            "\n".join(personas).strip(),
            "",
            "Hard constraints:",
            "- Do NOT propose modifying the repo directly (read-only takeover plan only).",
            "- Prefer small reversible deliveries (1 issue = 1 task).",
        ]
    ).strip()


def _write_bmad(project_dir: Path, bmad: dict[str, Any]) -> Path:
    bmad_dir = project_dir / "BMAD"
    bmad_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "PRODUCT_BRIEF.md": _safe_text(bmad.get("product_brief_md")),
        "PRD.md": _safe_text(bmad.get("prd_md")),
        "ARCHITECTURE.md": _safe_text(bmad.get("architecture_md")),
        "STORIES.md": _safe_text(bmad.get("stories_md")),
    }
    for filename, content in mapping.items():
        if not content:
            content = f"# {filename.replace('.md','').replace('_',' ').title()}\n\n- TBD\n"
        _write_text(bmad_dir / filename, content.strip() + "\n")
    return bmad_dir


def _append_chat(
    project_dir: Path,
    *,
    author: str,
    text: str,
    tags: list[str] | None = None,
    thread_tag: str | None = None,
    event: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "author": author,
        "text": text,
        "tags": tags or [],
        "mentions": [],
    }
    if event:
        payload["event"] = event
    _append_ndjson(project_dir / "chat" / "global.ndjson", payload)
    if thread_tag:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "", str(thread_tag or "").strip().lower())
        if safe:
            _append_ndjson(project_dir / "chat" / "threads" / f"{safe}.ndjson", payload)


def apply_takeover_wizard_output(
    *,
    projects_root: Path,
    project_id: str,
    output_payload: dict[str, Any],
    run_id: str,
    repo_path: Path,
    prompt_path: Path | None,
    runner: RunnerResult | None,
) -> TakeoverWizardResult:
    project_dir = projects_root / project_id
    runs_dir = project_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_json_path = runs_dir / f"{run_id}.json"
    output_md_path = runs_dir / f"{run_id}.md"

    is_valid, reason = _validate_output(output_payload)
    if not is_valid:
        raise ValueError(f"wizard_output_invalid:{reason}")

    _write_json(output_json_path, output_payload)

    bmad = output_payload.get("bmad") if isinstance(output_payload.get("bmad"), dict) else {}
    bmad_dir = _write_bmad(project_dir, bmad)

    # STATE / ROADMAP
    state_md_raw = output_payload.get("state_md")
    state_sections = output_payload.get("state_sections") if isinstance(output_payload.get("state_sections"), dict) else {}
    if isinstance(state_md_raw, str) and state_md_raw.strip():
        _write_text(project_dir / "STATE.md", state_md_raw.strip() + "\n")
    else:
        _write_text(project_dir / "STATE.md", _state_md_from_sections(state_sections))

    roadmap_sections = (
        output_payload.get("roadmap_sections") if isinstance(output_payload.get("roadmap_sections"), dict) else {}
    )
    _write_text(project_dir / "ROADMAP.md", _roadmap_md_from_sections(roadmap_sections))

    # DECISIONS
    decisions = output_payload.get("decisions_adrs") if isinstance(output_payload.get("decisions_adrs"), list) else []
    _append_decisions(project_dir / "DECISIONS.md", decisions)

    # Agent messages -> chat + state updates
    agent_messages = output_payload.get("agent_messages") if isinstance(output_payload.get("agent_messages"), list) else []
    for msg in agent_messages:
        if not isinstance(msg, dict):
            continue
        agent_id = _safe_text(msg.get("agent_id"))
        text = _safe_text(msg.get("text"))
        state_update = msg.get("state_update") if isinstance(msg.get("state_update"), dict) else {}
        if agent_id and text:
            _append_chat(project_dir, author=agent_id, text=text, tags=["wizard"], thread_tag="wizard")
        if agent_id and state_update:
            _apply_agent_state_update(project_dir, agent_id, state_update)

    # System summary
    summary_lines = [
        f"Takeover Wizard complete: {run_id}",
        f"- project_id={project_id}",
        f"- repo_path={repo_path}",
        f"- output_json={output_json_path}",
        f"- bmad_dir={bmad_dir}",
    ]
    if runner is not None:
        summary_lines.append(f"- runner_status={runner.status} success={runner.success}")
    if prompt_path is not None:
        summary_lines.append(f"- prompt_path={prompt_path}")
    _append_chat(project_dir, author="system", text="\n".join(summary_lines), tags=["wizard"], thread_tag="wizard")

    # Evidence md
    cmd = f"scripts/takeover_wizard.py --project-id {project_id} --repo-path {repo_path} --data-dir app --run-intake --headless"
    md_lines = [
        f"# Takeover Wizard Run - {run_id}",
        "",
        f"- timestamp_utc: {_utc_now_iso()}",
        f"- project_id: {project_id}",
        f"- projects_root: {projects_root}",
        f"- repo_path: {repo_path}",
        f"- command: {cmd}",
        "",
        "## Outputs",
        f"- {output_json_path}",
        f"- {bmad_dir}",
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
    md_lines.append("")
    _write_text(output_md_path, "\n".join(md_lines))

    return TakeoverWizardResult(
        status="ok",
        project_id=project_id,
        repo_path=str(repo_path),
        projects_root=str(projects_root),
        run_id=run_id,
        output_json_path=str(output_json_path),
        output_md_path=str(output_md_path),
        prompt_path=str(prompt_path) if prompt_path is not None else None,
        bmad_dir=str(bmad_dir),
        runner=runner,
        error=None,
    )


def run_takeover_wizard(
    *,
    projects_root: Path,
    project_id: str,
    repo_path: Path,
    l1_agents: list[str] | None = None,
    run_intake: bool = True,
    headless: bool = True,
    timeout_s: int = 240,
) -> TakeoverWizardResult:
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

    manager = BrainManager(projects_root=projects_root)

    intake: dict[str, Any] | None = None
    plan: dict[str, Any] | None = None
    questions: list[str] | None = None

    if run_intake:
        intake_result = manager.run_intake(project_id, repo_path)
        intake = dict(intake_result.intake or {})
        plan = dict(intake_result.plan or {})
        questions = list(intake_result.questions or [])
    else:
        # Fallback: scan minimal intake for prompt context.
        try:
            intake = scan_repo(repo_path)
        except Exception:
            intake = None

    l1 = _list_l1_agents(project_id, projects_root, l1_agents)

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "takeover_wizard_output.schema.json"
    if not schema_path.exists():
        # Repo layout fallback (app/schemas)
        schema_path = Path(__file__).resolve().parents[2] / "app" / "schemas" / "takeover_wizard_output.schema.json"

    prompt = _wizard_prompt(
        project_id=project_id,
        repo_path=repo_path,
        l1_agents=l1,
        intake=intake,
        plan=plan,
        questions=questions,
    )

    prompt_path = runs_dir / f"{run_id}_prompt.txt"
    _write_text(prompt_path, prompt + "\n")

    if not headless:
        # No headless run: write minimal placeholders and return.
        bmad_dir = project_dir / "BMAD"
        bmad_dir.mkdir(parents=True, exist_ok=True)
        for name in ["PRODUCT_BRIEF.md", "PRD.md", "ARCHITECTURE.md", "STORIES.md"]:
            _write_text(bmad_dir / name, f"# {name.replace('.md','')}\n\n- TBD\n")
        _append_chat(
            project_dir,
            author="system",
            text=f"Takeover Wizard prepared prompt only (headless disabled). Prompt: {prompt_path}",
            tags=["wizard"],
            thread_tag="wizard",
            event="takeover_wizard_prompt_only",
        )
        return TakeoverWizardResult(
            status="prompt_only",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id=run_id,
            output_json_path="",
            output_md_path="",
            prompt_path=str(prompt_path),
            bmad_dir=str(bmad_dir),
            runner=None,
            error=None,
        )

    runner_result = run_openrouter_exec(
        prompt,
        cwd=repo_path,
        timeout_s=timeout_s,
        sandbox_mode="read-only",
        approval_policy="never",
        output_schema_path=schema_path if schema_path.exists() else None,
        output_last_message_path=runs_dir / f"{run_id}_openrouter_output.json",
        ephemeral=True,
    )

    if not runner_result.success or not runner_result.output_text.strip():
        error = runner_result.error or "openrouter_exec_failed"
        _append_chat(
            project_dir,
            author="system",
            text=f"Takeover Wizard headless failed: {error}. Prompt saved at: {prompt_path}",
            tags=["wizard"],
            thread_tag="wizard",
            event="takeover_wizard_failed",
        )
        return TakeoverWizardResult(
            status="failed",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id=run_id,
            output_json_path="",
            output_md_path="",
            prompt_path=str(prompt_path),
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
            text=f"Takeover Wizard output JSON invalid: {error}. Prompt: {prompt_path}",
            tags=["wizard"],
            thread_tag="wizard",
            event="takeover_wizard_failed",
        )
        return TakeoverWizardResult(
            status="failed",
            project_id=project_id,
            repo_path=str(repo_path),
            projects_root=str(projects_root),
            run_id=run_id,
            output_json_path="",
            output_md_path="",
            prompt_path=str(prompt_path),
            bmad_dir=str(project_dir / "BMAD"),
            runner=runner_result,
            error=error,
        )

    if not isinstance(payload, dict):
        raise ValueError("wizard_output_invalid:root_not_object")

    # Force required identity fields in case the model drifts.
    payload.setdefault("wizard_version", WIZARD_VERSION)
    payload.setdefault("generated_at_utc", _utc_now_iso())
    payload.setdefault("project_id", project_id)
    payload.setdefault("repo_path", str(repo_path))

    return apply_takeover_wizard_output(
        projects_root=projects_root,
        project_id=project_id,
        output_payload=payload,
        run_id=run_id,
        repo_path=repo_path,
        prompt_path=prompt_path,
        runner=runner_result,
    )


def run_takeover_wizard_async(
    *,
    projects_root: Path,
    project_id: str,
    repo_path: Path,
    on_done: callable | None = None,
    on_error: callable | None = None,
    l1_agents: list[str] | None = None,
    run_intake: bool = True,
    headless: bool = True,
    timeout_s: int = 240,
) -> threading.Thread:
    def _run() -> None:
        try:
            result = run_takeover_wizard(
                projects_root=projects_root,
                project_id=project_id,
                repo_path=repo_path,
                l1_agents=l1_agents,
                run_intake=run_intake,
                headless=headless,
                timeout_s=timeout_s,
            )
        except Exception as exc:  # noqa: BLE001
            if on_error:
                on_error(str(exc))
            return
        if on_done:
            on_done(result)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
