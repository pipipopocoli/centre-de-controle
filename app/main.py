from __future__ import annotations

import fcntl
import json
import os
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
LOCK_PATH = Path.home() / ".cache" / "cockpit" / "singleton.lock"


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
    stamp = str(payload.get("stamp") or "").strip()
    if stamp:
        return stamp
    branch = str(payload.get("branch") or "").strip()
    sha = str(payload.get("sha") or "").strip()
    if not branch or not sha:
        return None
    dirty = payload.get("dirty")
    dirty_flag = ""
    if isinstance(dirty, bool) and dirty:
        dirty_flag = "*"
    elif isinstance(dirty, str) and dirty.strip() == "*":
        dirty_flag = "*"
    return f"{branch}@{sha}{dirty_flag}"


def _get_version_stamp() -> str:
    version_json = _resource_path("app", "version.json")
    if getattr(sys, "frozen", False):
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

    try:
        branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        sha = _run_git(["git", "rev-parse", "--short", "HEAD"])
        dirty = _run_git(["git", "status", "--porcelain"])
        dirty_flag = "*" if dirty else ""
        return f"{branch}@{sha}{dirty_flag}"
    except Exception:
        stamp = _read_version_json(version_json)
        if stamp:
            return stamp
        return "unknown@unknown"


def _get_repo_head() -> str:
    try:
        branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        sha = _run_git(["git", "rev-parse", "--short", "HEAD"])
        dirty = _run_git(["git", "status", "--porcelain"])
        dirty_flag = "*" if dirty else ""
        return f"{branch}@{sha}{dirty_flag}"
    except Exception:
        return "unavailable"


def _runtime_mode() -> str:
    override = str(os.environ.get("COCKPIT_RUNTIME_MODE") or "").strip().upper()
    if override in {"DEV LIVE", "RELEASE"}:
        return override
    return "RELEASE" if getattr(sys, "frozen", False) else "DEV LIVE"


def _runtime_source(projects_root: Path) -> str:
    repo_root = ROOT_DIR / "control" / "projects"
    app_root = Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"
    try:
        resolved = projects_root.expanduser().resolve()
    except OSError:
        resolved = projects_root
    if resolved == repo_root:
        return "repo"
    if resolved == app_root:
        return "appsupport"
    return "custom"


def main() -> int:
    # -- Singleton guard: prevent duplicate instances --------------------------
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(LOCK_PATH, "w")  # noqa: SIM115
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        from PySide6.QtWidgets import QMessageBox

        _app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Cockpit déjà ouvert",
            "Une instance du Centre de contrôle est déjà active.\n"
            "Ferme-la d'abord ou utilise-la.",
        )
        lock_file.close()
        return 1

    app = QApplication(sys.argv)
    app._singleton_lock = lock_file  # type: ignore[attr-defined]  # keep lock alive
    app.setStyleSheet(_read_stylesheet(THEME_PATH))

    watcher = QFileSystemWatcher([str(THEME_PATH)])
    watcher.fileChanged.connect(lambda _path: app.setStyleSheet(_read_stylesheet(THEME_PATH)))
    app._qss_watcher = watcher  # type: ignore[attr-defined]

    project = ensure_demo_project()
    projects = list_projects()

    app_stamp = _get_version_stamp()
    repo_head = _get_repo_head()
    runtime_mode = _runtime_mode()
    runtime_source = _runtime_source(PROJECTS_DIR)
    window = MainWindow(
        project,
        projects=projects,
        version_text=app_stamp,
        app_stamp=app_stamp,
        repo_head=repo_head,
        data_dir=str(PROJECTS_DIR),
        runtime_mode=runtime_mode,
        runtime_source=runtime_source,
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
