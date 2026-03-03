from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.ui.model_routing import ModelRoutingWidget  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    widget = ModelRoutingWidget()
    payload = {
        "voice_stt_model": "google/gemini-2.5-flash",
        "l1_model": "liquid/lfm-2.5-1.2b-thinking:free",
        "l2_scene_model": "arcee-ai/trinity-large-preview:free",
        "lfm_spawn_max": 6,
        "stream_enabled": False,
    }
    widget.set_profile_payload(payload)
    out = widget.profile_payload()
    assert out["voice_stt_model"] == payload["voice_stt_model"]
    assert out["l1_model"] == payload["l1_model"]
    assert out["l2_scene_model"] == payload["l2_scene_model"]
    assert out["lfm_spawn_max"] == payload["lfm_spawn_max"]
    assert out["stream_enabled"] == payload["stream_enabled"]
    app.quit()
    print("OK: ui model routing panel verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

