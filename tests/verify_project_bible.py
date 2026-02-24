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
    assert "Delta refresh" in html
    result = update_vulgarisation(project)
    assert result.snapshot_path.exists()
    assert result.html_path.exists()
    result_snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
    delta_result = result_snapshot.get("delta_since_last_refresh", {})
    assert isinstance(delta_result, dict), "missing delta_since_last_refresh"
    assert str(delta_result.get("status") or "").strip() in {"initial", "changed", "unchanged"}
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

        partial_dir = Path(tmp) / "brief-partial"
        _seed_project_files(partial_dir)
        (partial_dir / "STATE.md").write_text(
            "# State\n\n## Phase\n- Review\n\n## Objective\n- \n\n## Now\n- \n\n## Blockers\n- \n",
            encoding="utf-8",
        )
        (partial_dir / "ROADMAP.md").write_text(
            "# Roadmap\n\n## Next\n- \n\n## Risks\n- \n",
            encoding="utf-8",
        )
        partial_project = ProjectData(
            project_id="brief-partial",
            name="brief-partial",
            path=partial_dir,
            agents=[],
            roadmap={},
            settings={},
        )

        partial_first = update_vulgarisation(partial_project)
        partial_first_snapshot = json.loads(partial_first.snapshot_path.read_text(encoding="utf-8"))
        brief_rows = partial_first_snapshot.get("brief_60s")
        assert isinstance(brief_rows, dict), "brief_60s missing"
        for key in ("On est ou", "On va ou", "Pourquoi", "Comment"):
            assert str(brief_rows.get(key) or "").strip(), f"brief row is empty: {key}"
        retention_payload = partial_first_snapshot.get("retention_advisory")
        assert isinstance(retention_payload, dict), "retention_advisory missing"
        assert str(retention_payload.get("status") or "") == "missing", "retention should be missing when file absent"
        assert str(retention_payload.get("decision_tag") or "") == "defer", "missing retention should defer decision"

        partial_first_delta = partial_first_snapshot.get("delta_since_last_refresh", {})
        assert str(partial_first_delta.get("status") or "") == "initial", "first refresh must be initial"
        assert str(partial_first_delta.get("hint") or "").strip(), "delta hint missing for initial refresh"

        partial_second = update_vulgarisation(partial_project)
        partial_second_snapshot = json.loads(partial_second.snapshot_path.read_text(encoding="utf-8"))
        partial_second_delta = partial_second_snapshot.get("delta_since_last_refresh", {})
        assert str(partial_second_delta.get("status") or "") == "unchanged", "second refresh should be unchanged"
        assert str(partial_second_delta.get("previous_hash") or "") == str(
            partial_second_delta.get("current_hash") or ""
        ), "unchanged delta must keep same hash"

        (partial_dir / "STATE.md").write_text(
            "# State\n\n## Phase\n- Review\n\n## Objective\n- Lock runbook signal\n\n## Now\n- Validate operator digest\n",
            encoding="utf-8",
        )
        partial_third = update_vulgarisation(partial_project)
        partial_third_snapshot = json.loads(partial_third.snapshot_path.read_text(encoding="utf-8"))
        partial_third_delta = partial_third_snapshot.get("delta_since_last_refresh", {})
        assert str(partial_third_delta.get("status") or "") == "changed", "delta should be changed after source edit"
        assert str(partial_third_delta.get("previous_hash") or "") != str(
            partial_third_delta.get("current_hash") or ""
        ), "changed delta must update hash"
        partial_html = partial_third.html_path.read_text(encoding="utf-8")
        assert "Delta refresh" in partial_html
        assert "retention=" in partial_html.lower()

        overdue_dir = Path(tmp) / "retention-overdue"
        _seed_project_files(overdue_dir)
        (overdue_dir / "runs" / "retention").mkdir(parents=True, exist_ok=True)
        old_generated_at = "2026-02-20T08:00:00+00:00"
        overdue_next = "2026-02-20T09:00:00+00:00"
        (overdue_dir / "runs" / "retention" / "retention_status.json").write_text(
            json.dumps(
                {
                    "policy_version": "wave14-7-30-90-permanent-v1",
                    "project_id": "retention-overdue",
                    "generated_at": old_generated_at,
                    "next_compaction_at": overdue_next,
                    "sources": {},
                    "totals": {"hot_7d": 1, "warm_30d": 0, "cool_90d": 0, "archive_permanent": 0},
                    "archive_artifacts": [],
                    "isolation_check": {
                        "canonical_project_id": "retention-overdue",
                        "projects_root": str(overdue_dir.parent),
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        overdue_project = ProjectData(
            project_id="retention-overdue",
            name="retention-overdue",
            path=overdue_dir,
            agents=[],
            roadmap={},
            settings={},
        )
        overdue_result = update_vulgarisation(overdue_project)
        overdue_snapshot = json.loads(overdue_result.snapshot_path.read_text(encoding="utf-8"))
        overdue_retention = overdue_snapshot.get("retention_advisory")
        assert isinstance(overdue_retention, dict), "overdue retention payload missing"
        assert str(overdue_retention.get("status") or "") in {"warn", "critical"}, "overdue status must degrade"
        assert str(overdue_retention.get("decision_tag") or "") in {"defer", "reject"}
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
