from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def _normalize_projects_dir(path: Path) -> Path:
    # Accept either the projects root or the Cockpit base dir.
    if path.name == "Cockpit":
        return path / "projects"
    if path.name != "projects" and (path / "projects").exists():
        return path / "projects"
    return path


def _resolve_projects_dir() -> Path:
    env_value = os.environ.get("COCKPIT_DATA_DIR")
    if env_value:
        return _normalize_projects_dir(Path(env_value).expanduser())
    local_projects = ROOT_DIR / "control" / "projects"
    if local_projects.exists():
        return local_projects
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


PROJECTS_DIR = _resolve_projects_dir()
CONTROL_DIR = PROJECTS_DIR.parent


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id
