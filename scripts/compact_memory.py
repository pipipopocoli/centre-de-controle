#!/usr/bin/env python3
"""Memory compaction tool (local-first, deterministic).

Usage:
  ./.venv/bin/python scripts/compact_memory.py --project cockpit --agent clems
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]

MAX_LINES = 120
MAX_ITEMS = 5
MAX_SIGNALS = 10
MAX_SIGNAL_CHARS = 280

SECTION_ORDER = [
    "Role",
    "Facts / Constraints",
    "Decisions (refs ADR)",
    "Open Loops",
    "Now",
    "Next",
    "Blockers",
    "Links",
    "Recent Signals (autogen, last 10)",
]


def _read_lines(path: Path, max_lines: int = 400) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[:max_lines]


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current and line.lstrip().startswith("-"):
            item = line.lstrip("-").strip()
            if item:
                sections[current].append(item)
    return sections


def _extract_decisions(lines: list[str], max_items: int) -> list[str]:
    items: list[str] = []
    for raw in lines:
        if raw.startswith("## "):
            items.append(raw[3:].strip())
            if len(items) >= max_items:
                break
    return items


def _clean_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    placeholders = {"...", "(non defini)", "(none)"}
    for item in items:
        value = item.strip()
        if not value:
            continue
        if value in placeholders:
            continue
        cleaned.append(value)
    return cleaned


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _read_ndjson_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = lines[-limit:] if limit > 0 else lines
    output: list[dict[str, Any]] = []
    for raw in lines:
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            output.append(payload)
    return output


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _format_signal(payload: dict[str, Any], default_author: str) -> tuple[str | None, str]:
    timestamp = payload.get("timestamp")
    author = payload.get("author") or payload.get("agent_id") or payload.get("from") or default_author
    text = payload.get("text") or payload.get("content") or payload.get("event") or ""
    text = _truncate(str(text), MAX_SIGNAL_CHARS)
    if timestamp:
        return timestamp, f"[{timestamp}] {author}: {text}"
    return None, f"{author}: {text}"


def build_memory_proposal(project_id: str, agent_id: str) -> str:
    project_dir = ROOT_DIR / "control" / "projects" / project_id
    agent_dir = project_dir / "agents" / agent_id

    memory_path = agent_dir / "memory.md"
    state_path = project_dir / "STATE.md"
    decisions_path = project_dir / "DECISIONS.md"
    roadmap_path = project_dir / "ROADMAP.md"
    journal_path = agent_dir / "journal.ndjson"
    chat_path = project_dir / "chat" / "global.ndjson"

    memory_sections = _extract_sections(_read_lines(memory_path))
    state_sections = _extract_sections(_read_lines(state_path))
    roadmap_sections = _extract_sections(_read_lines(roadmap_path))
    decisions = _extract_decisions(_read_lines(decisions_path), MAX_ITEMS)

    def section_or_fallback(name: str, fallback: list[str]) -> list[str]:
        existing = _clean_items(memory_sections.get(name, []))
        if existing:
            return existing[:MAX_ITEMS]
        if fallback:
            return _dedup(fallback)[:MAX_ITEMS]
        return ["..."]

    now_items = state_sections.get("Now", [])
    next_items = state_sections.get("Next", [])
    blocker_items = state_sections.get("Blockers", [])
    risk_items = roadmap_sections.get("Risks", [])

    open_loops = _dedup(_clean_items(blocker_items) + _clean_items(risk_items))

    # Mentions from recent signals
    mention_items: list[str] = []
    for payload in _read_ndjson_tail(chat_path, 50):
        mentions = payload.get("mentions") or []
        for mention in mentions:
            mention_items.append(f"mention @{mention}")
    for payload in _read_ndjson_tail(journal_path, 50):
        if payload.get("event") == "mention":
            mention_items.append("mention recorded")
    if mention_items:
        open_loops.extend(_dedup(mention_items))

    # Recent signals (chat + journal)
    signals: list[tuple[datetime | None, int, str]] = []
    idx = 0
    for payload in _read_ndjson_tail(chat_path, 50):
        ts, line = _format_signal(payload, "chat")
        signals.append((_parse_iso(ts), idx, line))
        idx += 1
    for payload in _read_ndjson_tail(journal_path, 50):
        ts, line = _format_signal(payload, "journal")
        signals.append((_parse_iso(ts), idx, line))
        idx += 1
    signals.sort(key=lambda item: (item[0] is None, item[0], item[1]))
    recent_lines = [item[2] for item in signals][-MAX_SIGNALS:]

    sections: dict[str, list[str]] = {
        "Role": section_or_fallback("Role", []),
        "Facts / Constraints": section_or_fallback("Facts / Constraints", []),
        "Decisions (refs ADR)": section_or_fallback("Decisions (refs ADR)", decisions),
        "Open Loops": section_or_fallback("Open Loops", open_loops),
        "Now": section_or_fallback("Now", _clean_items(now_items)),
        "Next": section_or_fallback("Next", _clean_items(next_items)),
        "Blockers": section_or_fallback("Blockers", _clean_items(blocker_items)),
        "Links": section_or_fallback("Links", []),
        "Recent Signals (autogen, last 10)": recent_lines or ["(none)"],
    }

    lines: list[str] = [f"# Memory - {agent_id}", ""]
    for section in SECTION_ORDER:
        lines.append(f"## {section}")
        for item in sections.get(section, ["..."])[:MAX_ITEMS]:
            lines.append(f"- {item}")
        lines.append("")

    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]

    return "\n".join(lines).rstrip() + "\n"


def write_memory_proposal(project_id: str, agent_id: str, content: str) -> Path:
    path = ROOT_DIR / "control" / "projects" / project_id / "agents" / agent_id / "memory.proposed.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Memory compaction tool")
    parser.add_argument("--project", required=True)
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()

    content = build_memory_proposal(args.project, args.agent)
    path = write_memory_proposal(args.project, args.agent, content)
    line_count = len(content.strip().splitlines())
    print(f"Wrote {path}")
    print(f"Lines: {line_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
