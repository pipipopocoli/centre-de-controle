#!/usr/bin/env python3
"""
Project context startup verification.
"""

from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import resolve_startup_project_id
from app.services.session_state import load_ui_session, save_ui_session


def _check_startup_resolution() -> None:
    projects = ["cockpit", "demo", "motherload"]
    assert resolve_startup_project_id(projects, "cockpit") == "cockpit"
    assert resolve_startup_project_id(projects, "unknown") == "cockpit"
    assert resolve_startup_project_id(["demo"], None) == "demo"
    assert resolve_startup_project_id([], "cockpit") is None


def _check_session_state_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = Path(temp_dir) / "ui_session.json"
        payload = save_ui_session(
            last_project_id="cockpit",
            last_app_stamp="branch@abc123",
            path=session_file,
        )
        assert payload.get("last_project_id") == "cockpit"
        assert payload.get("last_app_stamp") == "branch@abc123"
        assert payload.get("last_selected_at")

        loaded = load_ui_session(session_file)
        assert loaded.get("last_project_id") == "cockpit"
        assert loaded.get("last_app_stamp") == "branch@abc123"
        assert loaded.get("last_selected_at")


def main() -> int:
    _check_startup_resolution()
    _check_session_state_roundtrip()
    print("OK verify_project_context_startup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
