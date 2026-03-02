from __future__ import annotations

import shutil
from pathlib import Path


EVOZINA_ROOT_ARTIFACTS = (
    "INTAKE.md",
    "QUESTIONS.md",
    "PLAN.md",
    "STARTUP_PACK.md",
)


def find_root_artifacts(project_dir: Path, artifact_names: tuple[str, ...] = EVOZINA_ROOT_ARTIFACTS) -> list[Path]:
    root = Path(project_dir).expanduser()
    return [root / name for name in artifact_names if (root / name).exists()]


def _dedupe_destination(path: Path) -> Path:
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}.from_cockpit_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def move_root_artifacts(
    *,
    cockpit_project_dir: Path,
    evozina_project_dir: Path,
    artifact_names: tuple[str, ...] = EVOZINA_ROOT_ARTIFACTS,
) -> dict[str, list[str]]:
    cockpit_dir = Path(cockpit_project_dir).expanduser()
    evozina_dir = Path(evozina_project_dir).expanduser()
    evozina_dir.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for source_path in find_root_artifacts(cockpit_dir, artifact_names):
        destination_path = _dedupe_destination(evozina_dir / source_path.name)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination_path))
        moved.append(str(destination_path))

    remaining = [str(path) for path in find_root_artifacts(cockpit_dir, artifact_names)]
    return {
        "moved": moved,
        "remaining": remaining,
    }
