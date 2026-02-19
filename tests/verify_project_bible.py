#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.data.model import ProjectData  # noqa: E402
from app.data.store import ensure_demo_project, load_project  # noqa: E402
from app.services.project_bible import build_project_bible_html, update_vulgarisation  # noqa: E402
from app.ui.project_bible import ProjectBibleWidget  # noqa: E402


def _seed_project_files(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "runs").mkdir(parents=True, exist_ok=True)
    (project_dir / "vulgarisation").mkdir(parents=True, exist_ok=True)
    (project_dir / "STATE.md").write_text(
        "# State\n\n## Phase\n- Implement\n\n## Objective\n- Validate cost estimator\n",
        encoding="utf-8",
    )
    (project_dir / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Next\n- Check CP-0031 estimator\n",
        encoding="utf-8",
    )
    (project_dir / "DECISIONS.md").write_text("# Decisions\n\n- none\n", encoding="utf-8")


def _panel_value(snapshot: dict, panel_id: str, label: str, default: str = "n/a") -> str:
    panels = snapshot.get("panels")
    if not isinstance(panels, list):
        return default
    for panel in panels:
        if not isinstance(panel, dict) or str(panel.get("panel_id") or "") != panel_id:
            continue
        items = panel.get("items")
        if not isinstance(items, list):
            return default
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("label") or "").strip().lower() == label.strip().lower():
                return str(item.get("value") or default)
    return default


def main() -> int:
    ensure_demo_project()
    project = load_project("demo")

    html = build_project_bible_html(project)
    assert "Vulgarisation" in html
    assert project.project_id in html
    assert "Project summary" in html
    result = update_vulgarisation(project)
    assert result.snapshot_path.exists()
    assert result.html_path.exists()
    print("OK: vulgarisation html generation")

    with tempfile.TemporaryDirectory() as tmp:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        previous_month = now.replace(day=1)
        if previous_month.month == 1:
            previous_month = previous_month.replace(year=previous_month.year - 1, month=12)
        else:
            previous_month = previous_month.replace(month=previous_month.month - 1)

        event_source_dir = Path(tmp) / "events-first"
        _seed_project_files(event_source_dir)
        (event_source_dir / "vulgarisation" / "costs.json").write_text(
            json.dumps({"api_cost_cad": 999.0}, indent=2),
            encoding="utf-8",
        )
        (event_source_dir / "runs" / "cost_events.ndjson").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "schema_version": "wave05_cost_event_v2",
                            "run_id": "run-current",
                            "project_id": "events-first",
                            "agent_id": "agent-11",
                            "provider": "codex",
                            "input_tokens": 100,
                            "output_tokens": 100,
                            "cached_tokens": 0,
                            "cached_input_tokens": 0,
                            "elapsed_ms": 10,
                            "currency": "CAD",
                            "cost_cad_estimate": 12.34,
                            "timestamp": now.isoformat(),
                            "ts": now.timestamp(),
                        }
                    ),
                    json.dumps(
                        {
                            "schema_version": "wave05_cost_event_v2",
                            "run_id": "run-old",
                            "project_id": "events-first",
                            "agent_id": "agent-11",
                            "provider": "codex",
                            "input_tokens": 100,
                            "output_tokens": 100,
                            "cached_tokens": 0,
                            "cached_input_tokens": 0,
                            "elapsed_ms": 10,
                            "currency": "CAD",
                            "cost_cad_estimate": 55.0,
                            "timestamp": previous_month.isoformat(),
                            "ts": previous_month.timestamp(),
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        events_project = ProjectData(
            project_id="events-first",
            name="events-first",
            path=event_source_dir,
            agents=[],
            roadmap={},
            settings={},
        )
        events_result = update_vulgarisation(events_project)
        events_snapshot = json.loads(events_result.snapshot_path.read_text(encoding="utf-8"))
        assert _panel_value(events_snapshot, "cost", "Monthly estimate") == "12.34 CAD"
        assert _panel_value(events_snapshot, "cost", "Cost events (month)") == "1"

        fallback_dir = Path(tmp) / "legacy-fallback"
        _seed_project_files(fallback_dir)
        (fallback_dir / "vulgarisation" / "costs.json").write_text(
            json.dumps({"api_cost_cad": 88.0}, indent=2),
            encoding="utf-8",
        )
        (fallback_dir / "runs" / "cost_events.ndjson").write_text(
            json.dumps(
                {
                    "schema_version": "wave05_cost_event_v2",
                    "run_id": "run-old",
                    "project_id": "legacy-fallback",
                    "agent_id": "agent-11",
                    "provider": "codex",
                    "input_tokens": 100,
                    "output_tokens": 100,
                    "cached_tokens": 0,
                    "cached_input_tokens": 0,
                    "elapsed_ms": 10,
                    "currency": "CAD",
                    "cost_cad_estimate": 5.0,
                    "timestamp": previous_month.isoformat(),
                    "ts": previous_month.timestamp(),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        fallback_project = ProjectData(
            project_id="legacy-fallback",
            name="legacy-fallback",
            path=fallback_dir,
            agents=[],
            roadmap={},
            settings={},
        )
        fallback_result = update_vulgarisation(fallback_project)
        fallback_snapshot = json.loads(fallback_result.snapshot_path.read_text(encoding="utf-8"))
        assert _panel_value(fallback_snapshot, "cost", "Monthly estimate") == "88.00 CAD"
        assert _panel_value(fallback_snapshot, "cost", "Cost events (month)") == "0"
    print("OK: monthly estimator source order verified")

    app = QApplication.instance() or QApplication([])
    widget = ProjectBibleWidget()
    widget.set_project(project, refresh=True)
    rendered = widget.view.toHtml()
    assert "Vulgarisation" in rendered
    assert "Project summary" in rendered
    print("OK: vulgarisation widget rendering")

    app.quit()
    print("OK: vulgarisation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
