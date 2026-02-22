#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, load_project  # noqa: E402
from app.services.project_bible import update_vulgarisation  # noqa: E402


REQUIRED_SECTION_IDS = [
    'id="project-summary"',
    'id="architecture-overview"',
    'id="timeline"',
    'id="progress-panel"',
    'id="cost-usage"',
    'id="skill-inventory"',
]


def main() -> int:
    ensure_demo_project()
    project = load_project("demo")
    result = update_vulgarisation(project)

    html = result.html_path.read_text(encoding="utf-8")

    for marker in REQUIRED_SECTION_IDS:
        assert marker in html, f"missing section marker: {marker}"

    assert "Skip to summary cards" in html, "missing keyboard skip link"
    assert html.count('tabindex="0"') >= 6, "expected keyboard focusable sections"

    # Accessibility fallback requirements for chart-like displays.
    assert "fallback table" in html.lower(), "missing fallback table text"

    # Timeline event text must expose lane and severity in plain text.
    assert "[lane=" in html, "missing lane marker in timeline event text"
    assert "severity=" in html, "missing severity marker in timeline event text"

    # Freshness thresholds must be explicit in text.
    lowered = html.lower()
    assert ("warn >24h" in lowered) or ("warn &gt;24h" in lowered), "missing warn threshold"
    assert ("critical >72h" in lowered) or ("critical &gt;72h" in lowered), "missing critical threshold"

    # No color-only signal: status labels are explicit text chips.
    assert ">OK<" in html or "OK</span>" in html
    assert "WARN" in html
    assert "CRITICAL" in html

    print("OK: vulgarisation accessibility verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
