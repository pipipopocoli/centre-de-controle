#!/usr/bin/env python3
"""Verify L3 recovery relaunch gates for all 6 active entrants."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1")
STATE_PATH = ROOT / "data" / "arena_state.json"
ACTIVE_L3 = ROOT / "ROUND-3" / "ACTIVE_L3"
MIN_LINES = 700

REQUIRED_SECTIONS = [
    "objective",
    "scope in/out",
    "architecture/workflow summary",
    "changelog vs previous version",
    "imported opponent ideas",
    "risk register",
    "test and qa gates",
    "dod checklist",
    "next round strategy",
    "now/next/blockers",
]


@dataclass
class GateResult:
    agent: str
    fight: str
    md_exists: bool
    html_exists: bool
    md_lines: int
    lines_ok: bool
    sections_ok: bool
    sections_hit: int
    skills_exact_3: bool
    skill_count: int
    verdict: str


def load_state() -> dict:
    if not STATE_PATH.exists():
        raise SystemExit(f"FAIL: missing state file {STATE_PATH}")
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def find_fight_by_agent(state: dict, agent_id: str) -> str | None:
    pairings = (state.get("l3") or {}).get("pairings") or []
    for pair in pairings:
        if pair.get("agent_a") == agent_id or pair.get("agent_b") == agent_id:
            return pair.get("fight")
    return None


def count_skill_markers(text: str) -> int:
    bullet_count = len(re.findall(r"(?mi)^\\s*[-*]\\s*skill\\s*:?\\s*$", text))
    if bullet_count:
        return bullet_count
    heading_count = len(re.findall(r"(?mi)^\\s*#{1,6}\\s*skill\\s+[1-9]\\d*\\b", text))
    return heading_count


def check_agent(state: dict, agent_id: str) -> GateResult:
    fight = find_fight_by_agent(state, agent_id) or "UNKNOWN"
    fight_dir = f"FIGHT-{fight[1:]}" if fight.startswith("F") else "FIGHT-UNKNOWN"
    submissions = ACTIVE_L3 / fight_dir / "SUBMISSIONS"

    md_path = submissions / f"{agent_id}_SUBMISSION_V3_FINAL.md"
    html_path = submissions / f"{agent_id}_FINAL_HTML" / "index.html"

    md_exists = md_path.exists()
    html_exists = html_path.exists()
    md_text = md_path.read_text(encoding="utf-8", errors="ignore") if md_exists else ""
    md_lines = md_text.count("\n") + 1 if md_exists else 0
    lines_ok = md_lines >= MIN_LINES

    low = md_text.lower()
    sections_hit = sum(1 for token in REQUIRED_SECTIONS if token in low)
    sections_ok = sections_hit == len(REQUIRED_SECTIONS)

    skill_count = count_skill_markers(md_text)
    skills_exact_3 = skill_count == 3

    verdict = "PASS"
    if not (md_exists and html_exists and lines_ok and sections_ok and skills_exact_3):
        verdict = "FAIL"

    return GateResult(
        agent=agent_id,
        fight=fight,
        md_exists=md_exists,
        html_exists=html_exists,
        md_lines=md_lines,
        lines_ok=lines_ok,
        sections_ok=sections_ok,
        sections_hit=sections_hit,
        skills_exact_3=skills_exact_3,
        skill_count=skill_count,
        verdict=verdict,
    )


def main() -> int:
    state = load_state()
    entries = (state.get("l3") or {}).get("entries") or []
    if not entries:
        print("FAIL: no L3 entries found in arena_state.json")
        return 1

    print("L3 Recovery Gate Check")
    print(f"- min_lines: {MIN_LINES}")
    print("- checks: md_exists html_exists lines sections skills_exact_3")
    print("")
    print(
        "agent\tfight\tmd\thtml\tlines\tline_gate\tsections\tskills\tverdict"
    )

    fails = 0
    for agent_id in entries:
        result = check_agent(state, agent_id)
        print(
            f"{result.agent}\t{result.fight}\t{result.md_exists}\t{result.html_exists}\t"
            f"{result.md_lines}\t{result.lines_ok}\t{result.sections_hit}/10\t"
            f"{result.skill_count}\t{result.verdict}"
        )
        if result.verdict != "PASS":
            fails += 1

    print("")
    if fails:
        print(f"FAIL: {fails}/{len(entries)} entrant(s) failed recovery gates.")
        return 1
    print(f"PASS: {len(entries)}/{len(entries)} entrants passed recovery gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

