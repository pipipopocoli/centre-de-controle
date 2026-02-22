#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, load_project  # noqa: E402
from app.services.project_bible import (  # noqa: E402
    freshness_status_from_hours,
    update_vulgarisation,
)


REQUIRED_PANEL_KEYS = {
    "panel_id",
    "status",
    "headline",
    "items",
    "fallback_text",
    "evidence_links",
    "freshness_hours",
}


def main() -> int:
    ensure_demo_project()
    project = load_project("demo")
    result = update_vulgarisation(project)

    vulg_dir = project.path / "vulgarisation"
    config_path = vulg_dir / "config.json"
    snapshot_path = vulg_dir / "snapshot.json"
    html_path = vulg_dir / "index.html"
    log_path = vulg_dir / "update.log"

    assert config_path.exists(), "missing config.json"
    assert snapshot_path.exists(), "missing snapshot.json"
    assert html_path.exists(), "missing index.html"
    assert log_path.exists(), "missing update.log"

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert isinstance(snapshot, dict), "snapshot must be an object"

    freshness = snapshot.get("freshness")
    assert isinstance(freshness, dict), "missing freshness object"
    assert freshness.get("warn_hours") == 24, "warn threshold must be 24h"
    assert freshness.get("critical_hours") == 72, "critical threshold must be 72h"

    assert freshness_status_from_hours(24.0, 24.0, 72.0) == "ok"
    assert freshness_status_from_hours(24.1, 24.0, 72.0) == "warn"
    assert freshness_status_from_hours(72.1, 24.0, 72.0) == "critical"

    source_snapshot = snapshot.get("source_snapshot")
    assert isinstance(source_snapshot, dict), "missing source_snapshot"
    assert source_snapshot.get("composite_hash"), "missing composite hash"

    delta = snapshot.get("delta_since_last_refresh")
    assert isinstance(delta, dict), "missing delta_since_last_refresh"
    required_delta_keys = {
        "status",
        "previous_hash",
        "current_hash",
        "previous_generated_at",
        "current_generated_at",
        "hint",
    }
    missing_delta = required_delta_keys - set(delta.keys())
    assert not missing_delta, f"missing delta keys: {sorted(missing_delta)}"
    assert str(delta.get("status") or "") in {"initial", "changed", "unchanged"}, "invalid delta status"
    assert str(delta.get("hint") or "").strip(), "delta hint must be non-empty"

    panels = snapshot.get("panels")
    assert isinstance(panels, list) and panels, "missing panels"

    for panel in panels:
        assert isinstance(panel, dict), "panel must be object"
        missing = REQUIRED_PANEL_KEYS - set(panel.keys())
        assert not missing, f"missing panel keys: {sorted(missing)}"
        evidence_links = panel.get("evidence_links")
        assert isinstance(evidence_links, list), "evidence_links must be list"
        for entry in evidence_links:
            assert isinstance(entry, dict), "evidence entry must be object"
            assert "label" in entry and "url" in entry and "exists" in entry
            if entry.get("exists"):
                assert str(entry.get("url") or "").startswith("file://")

    assert result.snapshot_path == snapshot_path
    assert result.html_path == html_path

    print("OK: vulgarisation contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
