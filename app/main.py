from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.paths import PROJECTS_DIR  # noqa: E402
from app.data.store import ensure_demo_project, list_projects, load_project, resolve_startup_project_id, runtime_backend_mode  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


def _resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)  # type: ignore[attr-defined]
    return ROOT_DIR.joinpath(*parts)


THEME_PATH = _resource_path("app", "ui", "theme.qss")
LOCK_PATH = Path.home() / ".cache" / "cockpit" / "singleton.lock"
RUNTIME_BACKEND_ENV = "COCKPIT_RUNTIME_BACKEND"
STRICT_WRITES_ENV = "COCKPIT_API_STRICT_WRITES"
API_BASE_URL_ENV = "COCKPIT_API_BASE_URL"
API_TIMEOUT_MS_ENV = "COCKPIT_API_HEALTHCHECK_TIMEOUT_MS"
BOOT_CLEANUP_ENV = "COCKPIT_ENABLE_BOOT_CLEANUP"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8100"
BOOT_CLEANUP_TARGETS = ("runs", "chat", "agents", "vulgarisation")


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


def _runtime_backend() -> str:
    return runtime_backend_mode()


def _api_base_url() -> str:
    value = str(os.environ.get(API_BASE_URL_ENV) or DEFAULT_API_BASE_URL).strip()
    return value.rstrip("/")


def _api_timeout_seconds() -> float:
    raw = str(os.environ.get(API_TIMEOUT_MS_ENV) or "1500").strip()
    try:
        timeout_ms = int(raw)
    except ValueError:
        timeout_ms = 1500
    return max(timeout_ms, 100) / 1000.0


def _check_api_health(base_url: str, timeout_seconds: float) -> tuple[bool, str]:
    url = f"{base_url}/healthz"
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(getattr(response, "status", response.getcode()))
            payload = response.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        return False, f"{url} unreachable: {exc}"
    except OSError as exc:
        return False, f"{url} error: {exc}"

    if status_code != 200:
        return False, f"{url} returned status {status_code}"

    if payload and "ok" not in payload.lower():
        return False, f"{url} unexpected payload"

    return True, "ok"


def _project_list_for_api_mode() -> tuple[object, list[str]]:
    project_ids = list_projects()
    preferred_project_id = str(os.environ.get("COCKPIT_PROJECT_ID") or "").strip() or None
    startup_project_id = resolve_startup_project_id(project_ids, preferred_project_id)
    if startup_project_id is None:
        raise RuntimeError("No local project mirror available in AppSupport.")
    project = load_project(startup_project_id)
    return project, project_ids


def _boot_cleanup(projects_root: Path) -> list[Path]:
    if not projects_root.exists():
        return []
    removed: list[Path] = []
    for project_path in projects_root.iterdir():
        if not project_path.is_dir() or project_path.name.startswith("_"):
            continue
        for folder_name in BOOT_CLEANUP_TARGETS:
            target_path = project_path / folder_name
            if not target_path.exists():
                continue
            if target_path.is_file():
                target_path.unlink(missing_ok=True)
            else:
                shutil.rmtree(target_path, ignore_errors=False)
            removed.append(target_path)
    return removed


def _maybe_boot_cleanup(projects_root: Path) -> list[Path]:
    if str(os.environ.get(BOOT_CLEANUP_ENV) or "").strip() != "1":
        print(
            f"[cockpit] boot cleanup disabled by default; "
            f"set {BOOT_CLEANUP_ENV}=1 for manual maintenance."
        )
        return []
    removed = _boot_cleanup(projects_root)
    print(f"[cockpit] boot cleanup enabled: removed {len(removed)} path(s).")
    return removed


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

    _maybe_boot_cleanup(PROJECTS_DIR)

    runtime_backend = _runtime_backend()
    if runtime_backend == "api":
        api_base_url = _api_base_url()
        healthy, details = _check_api_health(api_base_url, _api_timeout_seconds())
        if not healthy:
            QMessageBox.critical(
                None,
                "Cockpit API indisponible",
                "Mode strict API actif: impossible de démarrer sans backend.\n\n"
                f"Healthcheck: {api_base_url}/healthz\n"
                f"Détail: {details}\n\n"
                "Démarre l'API puis relance Cockpit:\n"
                "./.venv/bin/python scripts/run_cockpit_api.py --port 8100",
            )
            lock_file.close()
            return 2
        os.environ[STRICT_WRITES_ENV] = "1"
        try:
            project, projects = _project_list_for_api_mode()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                None,
                "Cockpit API strict - miroir local manquant",
                "Mode strict API actif et backend joignable, mais aucun projet local exploitable.\n\n"
                f"Détail: {exc}\n\n"
                "Initialise un projet via API (`POST /v1/projects`) puis relance Cockpit.",
            )
            lock_file.close()
            return 2
    else:
        os.environ.pop(STRICT_WRITES_ENV, None)
        project = ensure_demo_project()
        projects = list_projects()

    app_stamp = _get_version_stamp()
    repo_head = _get_repo_head()
    runtime_mode = _runtime_mode()
    runtime_source = _runtime_source(PROJECTS_DIR)
    if runtime_backend == "api":
        runtime_source = f"{runtime_source}+api-strict"
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
