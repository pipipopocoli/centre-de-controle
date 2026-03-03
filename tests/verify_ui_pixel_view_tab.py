from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.ui.pixel_view import PixelViewWidget  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    widget = PixelViewWidget()
    payload = {
        "project_id": "cockpit",
        "window": "24h",
        "bucket_minutes": 60,
        "generated_at_utc": "2026-03-03T00:00:00+00:00",
        "rows": [
            {
                "agent_id": "victor",
                "cells": [
                    {"bucket_start": "2026-03-03T00:00:00+00:00", "intensity": 1, "chat_messages": 1, "run_events": 0, "state_updates": 0},
                    {"bucket_start": "2026-03-03T01:00:00+00:00", "intensity": 2, "chat_messages": 0, "run_events": 1, "state_updates": 0},
                ],
            }
        ],
    }
    widget.set_feed(payload)
    assert widget.grid.rowCount() == 1
    assert widget.grid.columnCount() == 2
    assert "24h" in widget.status_label.text()
    app.quit()
    print("OK: ui pixel view tab verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

