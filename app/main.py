from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtWidgets import QApplication

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.paths import PROJECTS_DIR  # noqa: E402
from app.data.store import ensure_demo_project, list_projects  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


def _resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)  # type: ignore[attr-defined]
    return ROOT_DIR.joinpath(*parts)


THEME_PATH = _resource_path("app", "ui", "theme.qss")


def _read_stylesheet(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _read_version_json(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    branch = str(payload.get("branch") or "").strip()
    sha = str(payload.get("sha") or "").strip()
    if not branch or not sha:
        return None
    dirty = payload.get("dirty") is True
    dirty_flag = "*" if dirty else ""
    return f"{branch}@{sha}{dirty_flag}"


def _get_version_stamp() -> str:
    version_json = _resource_path("app", "version.json")
    stamp = _read_version_json(version_json)
    if stamp:
        return stamp

    try:
        branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        sha = _run_git(["git", "rev-parse", "--short", "HEAD"])
        dirty = _run_git(["git", "status", "--porcelain"])
        dirty_flag = "*" if dirty else ""
        return f"{branch}@{sha}{dirty_flag}"
    except Exception:
        return "unknown@unknown"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(_read_stylesheet(THEME_PATH))

    watcher = QFileSystemWatcher([str(THEME_PATH)])
    watcher.fileChanged.connect(lambda _path: app.setStyleSheet(_read_stylesheet(THEME_PATH)))
    app._qss_watcher = watcher  # type: ignore[attr-defined]

    project = ensure_demo_project()
    projects = list_projects()

    version_text = _get_version_stamp()
    window = MainWindow(project, projects=projects, version_text=version_text, data_dir=str(PROJECTS_DIR))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
