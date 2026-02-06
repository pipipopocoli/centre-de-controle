from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CONTROL_DIR = ROOT_DIR / "control"
PROJECTS_DIR = CONTROL_DIR / "projects"


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id
