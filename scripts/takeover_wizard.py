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


def _parse_csv(value: str) -> list[str]:
    items = []
    for raw in str(value or "").split(","):
        token = raw.strip()
        if token:
            items.append(token)
    return items


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Cockpit Takeover Wizard (BMAD + L1 roundtable).")
    parser.add_argument("--repo-path", required=True, help="Path to repo to take over (read-only for headless).")
    parser.add_argument("--project-id", default=None, help="Optional explicit project id.")
    parser.add_argument("--data-dir", default=None, help="Projects root. Special values: repo, app, or absolute path.")
    parser.add_argument(
        "--run-intake",
        dest="run_intake",
        action="store_true",
        default=True,
        help="Run deterministic intake first (default: enabled).",
    )
    parser.add_argument("--no-run-intake", dest="run_intake", action="store_false", help="Skip intake step.")
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=False,
        help="Run 1x headless Codex exec (read-only) and apply outputs.",
    )
    parser.add_argument(
        "--l1-agents",
        default="victor,leo,nova",
        help="Comma-separated L1 agent ids (default: victor,leo,nova).",
    )
    parser.add_argument("--timeout-s", type=int, default=240, help="Headless codex exec timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary output.")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).expanduser().resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_path}")
    if not repo_path.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

    projects_root = resolve_projects_root(args.data_dir, env=dict(os.environ))
    os.environ["COCKPIT_DATA_DIR"] = str(projects_root)

    from app.data.store import ensure_project_structure, project_dir  # noqa: E402
    from app.services.brain_manager import BrainManager  # noqa: E402
    from app.services.takeover_wizard import run_takeover_wizard  # noqa: E402

    manager = BrainManager(projects_root=projects_root)
    if args.project_id:
        project_id = str(args.project_id).strip()
        if not project_id:
            raise ValueError("project_id cannot be empty")
        ensure_project_structure(project_id, repo_path.name)
        _link_repo_settings(project_dir(project_id), project_id, repo_path)
    else:
        project_id = manager.create_project_from_repo(repo_path)

    l1_agents = _parse_csv(args.l1_agents)
    result = run_takeover_wizard(
        projects_root=projects_root,
        project_id=project_id,
        repo_path=repo_path,
        l1_agents=l1_agents if l1_agents else None,
        run_intake=bool(args.run_intake),
        headless=bool(args.headless),
        timeout_s=max(int(args.timeout_s), 30),
    )

    payload = {
        "status": result.status,
        "project_id": result.project_id,
        "repo_path": result.repo_path,
        "projects_root": result.projects_root,
        "run_id": result.run_id,
        "output_json_path": result.output_json_path,
        "output_md_path": result.output_md_path,
        "prompt_path": result.prompt_path,
        "bmad_dir": result.bmad_dir,
        "error": result.error,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"project_id={payload['project_id']}")
        print(f"run_id={payload['run_id']}")
        if payload["output_json_path"]:
            print(f"output_json_path={payload['output_json_path']}")
        if payload["output_md_path"]:
            print(f"output_md_path={payload['output_md_path']}")
        if payload["prompt_path"]:
            print(f"prompt_path={payload['prompt_path']}")
        print(f"bmad_dir={payload['bmad_dir']}")

    summary = (
        f"TakeoverWizardSummary status={payload['status']} project_id={payload['project_id']} "
        f"run_id={payload['run_id']} output_json={payload['output_json_path']}"
    )
    print(summary)

    return 0 if str(result.status) in {"ok", "prompt_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

