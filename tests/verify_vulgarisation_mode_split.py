#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import load_project
from app.services.project_bible import update_vulgarisation


def _count_primary_cards(html: str) -> int:
    return html.count("<article class='card")


def _extract_section(html: str, section_id: str) -> str:
    pattern = rf"<section id=\"{re.escape(section_id)}\".*?</section>"
    match = re.search(pattern, html, re.S)
    return match.group(0) if match else ""


def main() -> int:
    project = load_project("cockpit")

    simple_res = update_vulgarisation(project, mode="simple")
    simple_html = simple_res.html_path.read_text(encoding="utf-8")
    tech_res = update_vulgarisation(project, mode="tech")
    tech_html = tech_res.html_path.read_text(encoding="utf-8")

    # Simple mode contract
    assert _count_primary_cards(simple_html) <= 4, "simple mode should expose 4 primary cards max"
    assert "On est ou / On va ou / Pourquoi / Comment" in simple_html, "simple brief block missing"

    what_next_block = _extract_section(simple_html, "what-next")
    assert what_next_block, "simple mode missing what-next section"
    what_next_rows = max(what_next_block.count("<tr><td>") - 1, 0)
    assert what_next_rows <= 5, f"what-next must be <=5 rows, got {what_next_rows}"

    timeline_block = _extract_section(simple_html, "timeline")
    assert timeline_block, "simple mode missing timeline section"
    timeline_rows = max(timeline_block.count("<tr><td>") - 1, 0)
    assert timeline_rows <= 8, f"simple timeline must be <=8 rows, got {timeline_rows}"

    # Tech mode evidence sections
    required_tech_sections = [
        'id="architecture-overview"',
        'id="progress-panel"',
        'id="cost-usage"',
        'id="skill-inventory"',
    ]
    for marker in required_tech_sections:
        assert marker in tech_html, f"missing tech section marker: {marker}"

    print(
        "OK: vulgarisation mode split verified "
        f"(simple_cards={_count_primary_cards(simple_html)} what_next_rows={what_next_rows} timeline_rows={timeline_rows})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
