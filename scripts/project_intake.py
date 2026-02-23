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


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic project onboarding for existing repos.")
    parser.add_argument("--repo-path", required=True, help="Path to existing repository to onboard.")
    parser.add_argument("--project-id", default=None, help="Optional explicit project id.")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Projects root. Special values: repo, app, or absolute path.",
    )
    parser.add_argument(
        "--run-intake",
        dest="run_intake",
        action="store_true",
        default=True,
        help="Run full intake and startup pack generation (default: enabled).",
    )
    parser.add_argument(
        "--no-run-intake",
        dest="run_intake",
        action="store_false",
        help="Only attach repo without running intake.",
    )
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

    manager = BrainManager()
    if args.project_id:
        project_id = str(args.project_id).strip()
        if not project_id:
            raise ValueError("project_id cannot be empty")
        ensure_project_structure(project_id, repo_path.name)
        _link_repo_settings(project_dir(project_id), project_id, repo_path)
    else:
        project_id = manager.create_project_from_repo(repo_path)

    issue_seed_paths: list[str] = []
    startup_pack_path = str(project_dir(project_id) / "STARTUP_PACK.md")
    if args.run_intake:
        result = manager.run_intake(project_id, repo_path)
        issue_seed_paths = list(result.issue_seed_paths)
        startup_pack_path = str(result.startup_pack_path or startup_pack_path)

    payload = {
        "project_id": project_id,
        "project_dir": str(project_dir(project_id)),
        "projects_root": str(projects_root),
        "repo_path": str(repo_path),
        "run_intake": bool(args.run_intake),
        "startup_pack_path": startup_pack_path,
        "issue_seed_paths": sorted(issue_seed_paths),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"project_id={project_id}")
        print(f"project_dir={payload['project_dir']}")
        print(f"startup_pack_path={startup_pack_path}")
        print(f"issue_seed_count={len(issue_seed_paths)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
