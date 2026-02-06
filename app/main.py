from __future__ import annotations

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


THEME_PATH = Path(__file__).parent / "ui" / "theme.qss"


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


def _get_version_stamp() -> str:
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
