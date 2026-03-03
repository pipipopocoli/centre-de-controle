from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, list_projects, load_project  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


def _project_for_ui():
    project_ids = list_projects()
    if project_ids:
        return load_project(project_ids[0])
    return ensure_demo_project()


def main() -> int:
    app = QApplication.instance() or QApplication([])
    project = _project_for_ui()
    with patch.object(MainWindow, "run_auto_mode_tick", lambda self, manual=False: None):
        window = MainWindow(project=project, projects=[project.project_id])
    window.api_strict_mode = True

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(b"RIFF....WAVE")
        audio_path = Path(tmp.name)

    try:
        with patch("app.ui.main_window.QFileDialog.getOpenFileName", return_value=(str(audio_path), "wav")), patch(
            "app.ui.main_window.api_post_voice_transcribe",
            return_value={"text": "bonjour depuis audio", "status": "ok"},
        ):
            window.on_voice_transcribe_clicked()
        assert window.chatroom.input.text() == "bonjour depuis audio"
    finally:
        audio_path.unlink(missing_ok=True)

    app.quit()
    print("OK: ui voice button flow verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

