from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.analytics.pixel_feed import build_pixel_feed  # noqa: E402


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "cockpit"
        (project_dir / "chat").mkdir(parents=True, exist_ok=True)
        (project_dir / "runs").mkdir(parents=True, exist_ok=True)
        (project_dir / "agents" / "victor").mkdir(parents=True, exist_ok=True)

        (project_dir / "chat" / "global.ndjson").write_text(
            json.dumps({"timestamp": _utc_now_iso(), "author": "victor", "text": "chat ping"}) + "\n",
            encoding="utf-8",
        )
        (project_dir / "runs" / "AGENTIC_TURN_TEST.json").write_text(
            json.dumps(
                {
                    "generated_at_utc": _utc_now_iso(),
                    "messages": [{"author": "victor", "text": "run update"}],
                }
            ),
            encoding="utf-8",
        )
        (project_dir / "agents" / "victor" / "state.json").write_text(
            json.dumps({"updated_at": _utc_now_iso()}),
            encoding="utf-8",
        )

        payload = build_pixel_feed(project_dir=project_dir, project_id="cockpit", window="24h")
        assert payload["project_id"] == "cockpit"
        rows = payload.get("rows")
        assert isinstance(rows, list) and rows, payload
        victor_row = next((item for item in rows if item.get("agent_id") == "victor"), None)
        assert isinstance(victor_row, dict), rows
        cells = victor_row.get("cells")
        assert isinstance(cells, list) and cells, victor_row
        assert any(int(cell.get("intensity") or 0) > 0 for cell in cells), cells

    print("OK: pixel feed aggregation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

