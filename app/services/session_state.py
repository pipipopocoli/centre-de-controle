from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.paths import CONTROL_DIR


SESSION_FILE_NAME = "ui_session.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def session_path(control_dir: Path | None = None) -> Path:
    root = control_dir or CONTROL_DIR
    return root / SESSION_FILE_NAME


def load_ui_session(path: Path | None = None) -> dict[str, Any]:
    target = path or session_path()
    if not target.exists():
        return {}

    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}

    result: dict[str, Any] = {}
    last_project_id = payload.get("last_project_id")
    if isinstance(last_project_id, str) and last_project_id.strip():
        result["last_project_id"] = last_project_id.strip()

    last_selected_at = payload.get("last_selected_at")
    if isinstance(last_selected_at, str) and last_selected_at.strip():
        result["last_selected_at"] = last_selected_at.strip()

    last_app_stamp = payload.get("last_app_stamp")
    if isinstance(last_app_stamp, str) and last_app_stamp.strip():
        result["last_app_stamp"] = last_app_stamp.strip()

    return result



def save_ui_session(
    *,
    last_project_id: str | None = None,
    last_app_stamp: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    target = path or session_path()
    payload = load_ui_session(target)

    if last_project_id is not None:
        project_id = str(last_project_id).strip()
        payload["last_project_id"] = project_id or None
    if last_app_stamp is not None:
        stamp = str(last_app_stamp).strip()
        payload["last_app_stamp"] = stamp or None

    payload["last_selected_at"] = _utc_now_iso()

    target.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write pattern: write to temp file then rename
    # This prevents partial writes if the process crashes/interrupts
    try:
        with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as tmp:
            json.dump(payload, tmp, indent=2)
            tmp_path = Path(tmp.name)
        
        os.replace(tmp_path, target)
    except OSError:
        # If rename failed, try to clean up the temp file
        if 'tmp_path' in locals() and tmp_path.exists():
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise

    return payload
