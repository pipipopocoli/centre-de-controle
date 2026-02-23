from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.paths import PROJECTS_DIR, project_dir
from app.data.store import append_chat_message, ensure_project_structure, list_projects
from app.services.brainfs import ensure_profile
from app.services.project_intake import scan_repo
from app.services.question_builder import build_questions
from app.services.task_planner import build_plan


ISSUE_TEMPLATE = """# {issue_id} - {title}

- Owner: {owner}
- Phase: Plan
- Status: Todo
- Seed-Key: {seed_key}

## Objective
- {objective}

## Scope (In)
- {scope_in}

## Scope (Out)
- {scope_out}

## Now
- Pending kickoff

## Next
- Start task

## Blockers
- None

## Done (Definition)
- {done}

## Links
- STATE.md:
- DECISIONS.md:
- PR:

## Risks
- {risks}
"""


@dataclass
class IntakeResult:
    project_id: str
    intake: dict[str, Any]
    questions: list[str]
    plan: dict[str, Any]
    issue_seed_paths: list[str] = field(default_factory=list)
    startup_pack_path: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    cleaned = "-".join([part for part in cleaned.split("-") if part])
    return cleaned or "project"


def _next_issue_number(issues_dir: Path) -> int:
    max_num = 0
    pattern = re.compile(r"^ISSUE-(\d{4})(?:-|$)")
    if issues_dir.exists():
        for path in issues_dir.glob("ISSUE-*.md"):
            stem = path.stem
            match = pattern.match(stem)
            if not match:
                continue
            number = int(match.group(1))
            max_num = max(max_num, number)
    return max_num + 1


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _issue_filename(issue_number: int, title: str) -> str:
    slug = _slugify(title)[:48]
    return f"ISSUE-{issue_number:04d}-{slug}.md"


def _seed_key(owner: str, title: str) -> str:
    return f"startup_seed:{_slugify(owner)}:{_slugify(title)}"


def _normalize_linked_repo(raw_path: str) -> Path | None:
    value = str(raw_path or "").strip()
    if not value:
        return None
    candidate = Path(value).expanduser()
    try:
        return candidate.resolve()
    except OSError:
        return candidate.absolute()


class BrainManager:
    def __init__(self, projects_root: Path | None = None) -> None:
        self.projects_root = projects_root or PROJECTS_DIR

    def _project_path(self, project_id: str) -> Path:
        return self.projects_root / project_id

    def _project_ids(self) -> list[str]:
        if not self.projects_root.exists():
            return []
        ids: list[str] = []
        for entry in sorted(self.projects_root.iterdir(), key=lambda item: item.name):
            if not entry.is_dir() or entry.name == "_archive":
                continue
            ids.append(entry.name)
        return ids

    def _find_project_by_linked_repo(self, repo_path: Path) -> str | None:
        normalized_repo = _normalize_linked_repo(str(repo_path))
        if normalized_repo is None or not self.projects_root.exists():
            return None

        for project_id in self._project_ids():
            settings_path = self._project_path(project_id) / "settings.json"
            if not settings_path.exists():
                continue
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(settings, dict):
                continue
            linked = _normalize_linked_repo(str(settings.get("linked_repo_path") or ""))
            if linked is None:
                continue
            if linked == normalized_repo:
                return project_id
        return None

    def _unique_project_id(self, base: str) -> str:
        existing = set(self._project_ids()) or set(list_projects())
        if base not in existing:
            return base
        idx = 2
        while f"{base}-{idx}" in existing:
            idx += 1
        return f"{base}-{idx}"

    def create_project_from_repo(self, repo_path: Path) -> str:
        repo_path = repo_path.expanduser().resolve()
        existing_project_id = self._find_project_by_linked_repo(repo_path)
        project_id = existing_project_id or self._unique_project_id(_slugify(repo_path.name))
        ensure_project_structure(project_id, repo_path.name)
        settings_path = self._project_path(project_id) / "settings.json"
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        else:
            settings = {}
        settings["project_name"] = repo_path.name
        settings["linked_repo_path"] = str(repo_path)
        settings["updated_at"] = _utc_now_iso()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        return project_id

    def run_intake(self, project_id: str, repo_path: Path) -> IntakeResult:
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
        if not repo_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {repo_path}")

        try:
            intake = scan_repo(repo_path)
            if not intake:
                raise ValueError("Repo scan returned empty data")
            
            profile = ensure_profile(project_id, intake.get("stack") or [])
            questions = build_questions(intake)
            plan = build_plan(intake) or {"summary": "No plan generated", "tasks": []}

            self._write_intake_files(project_id, intake, profile, questions, plan)
            issue_seed_paths = self._write_issue_files(project_id, plan)
            startup_pack_path = self._write_startup_pack(project_id, intake, plan, issue_seed_paths)
            self._post_intake_message(project_id, intake, questions)
            self._update_state(project_id, intake, plan)

            return IntakeResult(
                project_id=project_id,
                intake=intake,
                questions=questions,
                plan=plan,
                issue_seed_paths=issue_seed_paths,
                startup_pack_path=str(startup_pack_path),
            )
        except Exception as e:
            # Fallback/Safety: Ensure project state is at least valid enough to debug
            error_msg = f"Brain Manager Intake Failed: {e}"
            append_chat_message(
                project_id,
                {
                    "timestamp": _utc_now_iso(),
                    "author": "system",
                    "text": error_msg,
                    "tags": ["error", "intake"],
                    "mentions": ["operator"],
                },
            )
            # Re-raise so caller knows it failed
            raise

    def _write_intake_files(
        self,
        project_id: str,
        intake: dict[str, Any],
        profile: dict[str, Any],
        questions: list[str],
        plan: dict[str, Any],
    ) -> None:
        pdir = project_dir(project_id)
        intake_path = pdir / "INTAKE.md"
        questions_path = pdir / "QUESTIONS.md"
        plan_path = pdir / "PLAN.md"

        summary_lines = [
            f"# Intake - {intake.get('project_name', project_id)}",
            "",
            f"- Repo: {intake.get('repo_path', '')}",
            f"- Stack: {', '.join(intake.get('stack') or [])}",
            f"- Files scanned: {intake.get('stats', {}).get('files_scanned', 0)}",
            f"- Scanned at: {intake.get('scanned_at', '')}",
            "",
            "## Risks",
        ]
        risks = intake.get("risks") or []
        if risks:
            summary_lines.extend([f"- {risk}" for risk in risks])
        else:
            summary_lines.append("- None detected")
        summary_lines += [
            "",
            "## Top files",
        ]
        for path in intake.get("top_files", [])[:20]:
            summary_lines.append(f"- {path}")
        summary_lines += [
            "",
            "## BrainFS profile",
            f"- Skills: {', '.join(profile.get('skills', []))}",
        ]
        _write_text(intake_path, "\n".join(summary_lines) + "\n")

        question_lines = ["# Questions", ""]
        for idx, q in enumerate(questions, 1):
            question_lines.append(f"{idx}. {q}")
        _write_text(questions_path, "\n".join(question_lines) + "\n")

        plan_lines = [
            f"# Plan - {intake.get('project_name', project_id)}",
            "",
            plan.get("summary", ""),
            "",
            "## Tasks",
        ]
        for task in plan.get("tasks", []):
            plan_lines.append(f"- {task.get('agent_id')}: {task.get('objective')}")
        _write_text(plan_path, "\n".join(plan_lines) + "\n")

    def _write_issue_files(self, project_id: str, plan: dict[str, Any]) -> list[str]:
        issues_dir = project_dir(project_id) / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        issue_number = _next_issue_number(issues_dir)
        seed_to_path: dict[str, Path] = {}
        signature_to_path: dict[tuple[str, str], Path] = {}

        for existing in sorted(issues_dir.glob("ISSUE-*.md")):
            try:
                content = existing.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            owner = ""
            title = ""
            seed_key = ""
            for line in lines:
                if line.startswith("# ") and " - " in line:
                    title = line.split(" - ", 1)[1].strip()
                elif line.startswith("- Owner:"):
                    owner = line.split(":", 1)[1].strip()
                elif line.startswith("- Seed-Key:"):
                    seed_key = line.split(":", 1)[1].strip()
            if seed_key:
                seed_to_path[seed_key] = existing
            if owner and title:
                signature_to_path[(owner, title)] = existing

        issue_seed_paths: list[str] = []

        for task in plan.get("tasks", []):
            owner = task.get("agent_id", "clems")
            title = task.get("objective", "Task")
            seed_key = _seed_key(owner, title)
            signature = (owner, title)
            existing_path = seed_to_path.get(seed_key) or signature_to_path.get(signature)
            if existing_path is not None:
                issue_seed_paths.append(str(existing_path))
                continue

            issue_id = f"ISSUE-{issue_number:04d}"
            filename = _issue_filename(issue_number, title)
            scope_in = task.get("scope", "TBD")
            scope_out = "Out of scope"
            done = task.get("done", "Definition of done required")
            risks = "Scope unclear"
            body = ISSUE_TEMPLATE.format(
                issue_id=issue_id,
                title=title,
                owner=owner,
                objective=title,
                scope_in=scope_in,
                scope_out=scope_out,
                done=done,
                risks=risks,
                seed_key=seed_key,
            )
            issue_path = issues_dir / filename
            _write_text(issue_path, body)
            seed_to_path[seed_key] = issue_path
            signature_to_path[signature] = issue_path
            issue_seed_paths.append(str(issue_path))
            issue_number += 1
        return sorted(issue_seed_paths)

    def _write_startup_pack(
        self,
        project_id: str,
        intake: dict[str, Any],
        plan: dict[str, Any],
        issue_seed_paths: list[str],
    ) -> Path:
        startup_pack_path = project_dir(project_id) / "STARTUP_PACK.md"
        project_name = str(intake.get("project_name") or project_id).strip() or project_id
        stack = ", ".join(intake.get("stack") or ["unknown"])
        repo_path = str(intake.get("repo_path") or "").strip()
        risks = intake.get("risks") if isinstance(intake.get("risks"), list) else []
        tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []

        lines = [
            "# Startup Pack",
            "",
            "## Objective",
            f"- Onboard existing repo {project_name} with deterministic intake and gate-ready dispatch.",
            "",
            "## Scope (In)",
            f"- Repo path: {repo_path}",
            f"- Stack detected: {stack}",
            "- Generate INTAKE.md, QUESTIONS.md, PLAN.md, STARTUP_PACK.md.",
            "- Seed startup issues without duplicates.",
            "",
            "## Scope (Out)",
            "- No tournament activation.",
            "- No runtime dispatch behavior change in onboarding step.",
            "",
            "## Initial risks",
        ]
        if risks:
            lines.extend(f"- {item}" for item in risks)
        else:
            lines.append("- None detected by intake scan.")

        lines += [
            "",
            "## Issue seeds",
        ]
        if issue_seed_paths:
            lines.extend(f"- {path}" for path in sorted(issue_seed_paths))
        else:
            lines.append("- None")

        lines += [
            "",
            "## Dispatch hints",
            f"- Canonical onboarding command: scripts/project_intake.py --repo-path {repo_path} --json",
            "- Optional cadence pulse: scripts/auto_mode.py --project cockpit --data-dir app --once --max-actions 0 --no-open --no-clipboard --no-notify",
            "",
            "## Seed summary",
        ]
        if tasks:
            for task in tasks:
                owner = str(task.get("agent_id") or "unassigned").strip() or "unassigned"
                objective = str(task.get("objective") or "Task").strip() or "Task"
                lines.append(f"- {owner}: {objective}")
        else:
            lines.append("- No tasks generated.")

        _write_text(startup_pack_path, "\n".join(lines) + "\n")
        return startup_pack_path

    def _post_intake_message(self, project_id: str, intake: dict[str, Any], questions: list[str]) -> None:
        summary = f"Intake complete. Stack: {', '.join(intake.get('stack') or [])}."
        if questions:
            summary += " Questions ready in QUESTIONS.md."
        append_chat_message(
            project_id,
            {
                "timestamp": _utc_now_iso(),
                "author": "clems",
                "text": summary,
                "tags": ["intake"],
                "mentions": [],
            },
        )

    def _update_state(self, project_id: str, intake: dict[str, Any], plan: dict[str, Any]) -> None:
        state_path = project_dir(project_id) / "STATE.md"
        objective = intake.get("project_name", project_id)
        next_items = [task.get("objective", "Task") for task in plan.get("tasks", [])[:3]]
        lines = [
            "# State",
            "## Phase",
            "- Plan",
            "## Objective",
            f"- Intake for {objective}",
            "## Now",
            "- Intake complete",
            "## Next",
        ]
        if next_items:
            lines.extend([f"- {item}" for item in next_items])
        else:
            lines.append("- Collect requirements")
        lines += [
            "## In Progress",
            "- None",
            "## Blockers",
            "- None",
            "## Risks",
            "- Intake pending operator answers",
            "## Links",
            "- INTAKE.md",
            "- QUESTIONS.md",
            "- PLAN.md",
        ]
        _write_text(state_path, "\n".join(lines) + "\n")
