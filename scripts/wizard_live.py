#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import resolve_projects_root  # noqa: E402


def _link_repo_settings(project_dir: Path, project_id: str, repo_path: Path) -> None:
    settings_path = project_dir / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}
    if not isinstance(settings, dict):
        settings = {}
    settings["project_id"] = project_id
    settings["project_name"] = repo_path.name
    settings["linked_repo_path"] = str(repo_path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def _resolve_repo_path(project_dir: Path, explicit_repo_path: str | None) -> Path:
    if explicit_repo_path:
        candidate = Path(explicit_repo_path).expanduser().resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Repository path not found: {candidate}")
        if not candidate.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {candidate}")
        return candidate

    settings_path = project_dir / "settings.json"
    if not settings_path.exists():
        raise FileNotFoundError(f"Missing settings file for project: {project_dir}")
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid settings.json for project: {project_dir}") from exc
    if not isinstance(settings, dict):
        raise ValueError(f"Invalid settings payload for project: {project_dir}")
    raw = str(settings.get("linked_repo_path") or "").strip()
    if not raw:
        raise ValueError(f"No linked_repo_path configured for project: {project_dir.name}")
    candidate = Path(raw).expanduser().resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Linked repository path not found: {candidate}")
    if not candidate.is_dir():
        raise NotADirectoryError(f"Linked repository path is not a directory: {candidate}")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Cockpit Wave19 Wizard Live controller.")
    parser.add_argument("action", choices=["start", "run", "stop"], help="Action to execute.")
    parser.add_argument("--project-id", default=None, help="Project id.")
    parser.add_argument("--repo-path", default=None, help="Repository path (required for start/run if no linked repo).")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Projects root. Special values: repo, app, or absolute path.",
    )
    parser.add_argument("--trigger", default="cli", help="Trigger label for logs.")
    parser.add_argument("--operator-message", default="", help="Operator message passed to wizard turn.")
    parser.add_argument("--timeout-s", type=int, default=240, help="Headless timeout in seconds.")
    parser.add_argument(
        "--no-run-initial",
        action="store_true",
        help="For start action only: do not execute initial run.",
    )
    parser.add_argument(
        "--include-full-intake",
        action="store_true",
        help="For run action only: include intake artifacts in context bridge.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary output.")
    args = parser.parse_args()

    projects_root = resolve_projects_root(args.data_dir, env=dict(os.environ))
    os.environ["COCKPIT_DATA_DIR"] = str(projects_root)

    from app.data.store import ensure_project_structure, project_dir  # noqa: E402
    from app.services.brain_manager import BrainManager  # noqa: E402
    from app.services.wizard_live import (  # noqa: E402
        run_wizard_live_turn,
        start_wizard_live_session,
        stop_wizard_live_session,
    )

    manager = BrainManager(projects_root=projects_root)
    repo_path: Path | None = None
    if args.action in {"start", "run"}:
        if args.repo_path:
            repo_path = Path(args.repo_path).expanduser().resolve()
            if not repo_path.exists():
                raise FileNotFoundError(f"Repository path not found: {repo_path}")
            if not repo_path.is_dir():
                raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

    if args.project_id:
        project_id = str(args.project_id).strip()
        if not project_id:
            raise ValueError("project_id cannot be empty")
        ensure_project_structure(project_id, (repo_path.name if repo_path is not None else project_id))
        if repo_path is not None:
            _link_repo_settings(project_dir(project_id), project_id, repo_path)
    elif repo_path is not None:
        project_id = manager.create_project_from_repo(repo_path)
    else:
        project_id = os.environ.get("COCKPIT_PROJECT_ID") or "cockpit"

    pdir = project_dir(project_id)
    if args.action in {"start", "run"}:
        repo_path = _resolve_repo_path(pdir, args.repo_path)

    if args.action == "start":
        result = start_wizard_live_session(
            projects_root=projects_root,
            project_id=project_id,
            repo_path=repo_path or Path("."),
            operator_message=str(args.operator_message or ""),
            trigger=str(args.trigger or "cli_start"),
            timeout_s=max(int(args.timeout_s), 30),
            run_initial=not bool(args.no_run_initial),
        )
    elif args.action == "run":
        from app.services.wizard_live import load_wizard_live_session  # noqa: E402

        session_payload = load_wizard_live_session(projects_root, project_id)
        session_active = bool(session_payload.get("active"))
        result = run_wizard_live_turn(
            projects_root=projects_root,
            project_id=project_id,
            repo_path=repo_path or Path("."),
            trigger=str(args.trigger or "cli_run"),
            operator_message=str(args.operator_message or ""),
            include_full_intake=bool(args.include_full_intake),
            timeout_s=max(int(args.timeout_s), 30),
            session_active=session_active,
        )
    else:
        result = stop_wizard_live_session(
            projects_root=projects_root,
            project_id=project_id,
            trigger=str(args.trigger or "cli_stop"),
            reason=str(args.operator_message or ""),
        )

    payload = {
        "status": result.status,
        "project_id": result.project_id,
        "repo_path": result.repo_path,
        "projects_root": result.projects_root,
        "run_id": result.run_id,
        "trigger": result.trigger,
        "session_active": result.session_active,
        "output_json_path": result.output_json_path,
        "output_md_path": result.output_md_path,
        "prompt_path": result.prompt_path,
        "context_path": result.context_path,
        "bmad_dir": result.bmad_dir,
        "error": result.error,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"project_id={payload['project_id']}")
        if payload["run_id"]:
            print(f"run_id={payload['run_id']}")
        if payload["output_json_path"]:
            print(f"output_json_path={payload['output_json_path']}")
        if payload["output_md_path"]:
            print(f"output_md_path={payload['output_md_path']}")
        if payload["prompt_path"]:
            print(f"prompt_path={payload['prompt_path']}")
        if payload["context_path"]:
            print(f"context_path={payload['context_path']}")
        print(f"session_active={str(bool(payload['session_active'])).lower()}")
        if payload["error"]:
            print(f"error={payload['error']}")

    summary = (
        f"WizardLiveSummary status={payload['status']} project_id={payload['project_id']} "
        f"run_id={payload['run_id']} session_active={str(bool(payload['session_active'])).lower()} "
        f"output_json={payload['output_json_path']}"
    )
    print(summary)

    return 0 if str(result.status) in {"ok", "started", "stopped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
