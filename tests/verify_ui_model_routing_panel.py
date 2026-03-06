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
        "clems_model": "anthropic/claude-sonnet-4.6",
        "l1_models": {
            "victor": "openai/gpt-5.4",
            "leo": "moonshotai/kimi-k2.5",
            "nova": "google/gemini-3.1-pro-preview",
            "vulgarisation": "moonshotai/kimi-k2.5",
        },
        "l2_default_model": "minimax/minimax-m2.5",
        "lfm_spawn_max": 6,
        "stream_enabled": False,
    }
    widget.set_profile_payload(payload)
    out = widget.profile_payload()
    assert out["voice_stt_model"] == payload["voice_stt_model"]
    assert out["clems_model"] == payload["clems_model"]
    assert out["l1_models"]["victor"] == payload["l1_models"]["victor"]
    assert out["l2_default_model"] == payload["l2_default_model"]
    assert out["lfm_spawn_max"] == payload["lfm_spawn_max"]
    assert out["stream_enabled"] == payload["stream_enabled"]
    app.quit()
    print("OK: ui model routing panel verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
