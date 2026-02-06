from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from app.data.paths import project_dir
from app.data.store import load_chat_global, load_chat_thread


Mode = Literal["light", "full"]


def _read_lines(path: Path, max_lines: int) -> list[str]:
    if max_lines <= 0 or not path.exists():
        return []
    return [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()][:max_lines]


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
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
    for line in lines:
        if line.startswith("## "):
            items.append(line[3:].strip())
            if len(items) >= max_items:
                break
    return items


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _read_open_issues(project_id: str, max_items: int = 10) -> list[str]:
    issues_dir = project_dir(project_id) / "issues"
    if not issues_dir.exists():
        return []
    issues: list[str] = []
    for path in sorted(issues_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if "Status: Done" in content:
            continue
        title = path.name
        for line in content.splitlines():
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
        issues.append(title)
        if len(issues) >= max_items:
            break
    return issues


def _format_chat_messages(messages: list[dict], max_chars: int, max_items: int) -> list[str]:
    lines: list[str] = []
    for payload in messages[:max_items]:
        timestamp = payload.get("timestamp", "")
        author = payload.get("author") or payload.get("agent_id") or "operator"
        text = _truncate(str(payload.get("text", "")), max_chars)
        if timestamp:
            lines.append(f"- [{timestamp}] {author}: {text}")
        else:
            lines.append(f"- {author}: {text}")
    return lines


def build_pack_context(project_id: str, mode: Mode, thread_tag: str | None = None) -> str:
    is_light = mode == "light"
    chat_limit = 20 if is_light else 200
    chat_max_chars = 280 if is_light else 800
    max_lines = 30 if is_light else 120

    state_lines = _read_lines(project_dir(project_id) / "STATE.md", 200)
    roadmap_lines = _read_lines(project_dir(project_id) / "ROADMAP.md", 200)
    decisions_lines = _read_lines(project_dir(project_id) / "DECISIONS.md", 400)

    state_sections = _extract_sections(state_lines)
    roadmap_sections = _extract_sections(roadmap_lines)

    objective = state_sections.get("Objective") or roadmap_sections.get("Now") or []
    phase = (state_sections.get("Phase") or [""])[0]
    now_items = state_sections.get("Now") or roadmap_sections.get("Now") or []
    next_items = state_sections.get("Next") or roadmap_sections.get("Next") or []
    risk_items = state_sections.get("Risks") or roadmap_sections.get("Risks") or []

    decision_items = _extract_decisions(decisions_lines, 2 if is_light else 10)
    open_issues = _read_open_issues(project_id, max_items=3 if is_light else 10)

    chat_messages = load_chat_global(project_id, limit=chat_limit)
    chat_lines = _format_chat_messages(chat_messages, chat_max_chars, 8 if is_light else chat_limit)

    thread_lines: list[str] = []
    if thread_tag:
        thread_messages = load_chat_thread(project_id, thread_tag, limit=20)
        thread_lines = _format_chat_messages(thread_messages, chat_max_chars, 10)

    parts: list[str] = []
    parts.append("Objectif")
    if objective:
        parts.extend(f"- {item}" for item in objective[:1 if is_light else 5])
    else:
        parts.append("- (non defini)")

    parts.append("")
    parts.append("Etat")
    if phase:
        parts.append(f"- Phase: {phase}")
    for item in now_items[:1 if is_light else 5]:
        parts.append(f"- Now: {item}")
    for item in next_items[:1 if is_light else 5]:
        parts.append(f"- Next: {item}")
    if not phase and not now_items and not next_items:
        parts.append("- (pas de state)")

    parts.append("")
    parts.append("Decisions")
    if decision_items:
        parts.extend(f"- {item}" for item in decision_items)
    else:
        parts.append("- (aucune)")

    parts.append("")
    parts.append("Taches ouvertes")
    if open_issues:
        parts.extend(f"- {issue}" for issue in open_issues)
    else:
        parts.append("- (aucune)")

    parts.append("")
    parts.append(f"Chat (last {chat_limit})")
    if chat_lines:
        parts.extend(chat_lines)
    else:
        parts.append("- (aucun message)")

    if thread_tag:
        parts.append("")
        parts.append(f"Thread #{thread_tag} (last 20)")
        if thread_lines:
            parts.extend(thread_lines)
        else:
            parts.append("- (aucun message)")

    parts.append("")
    parts.append("Risques")
    if risk_items:
        parts.extend(f"- {item}" for item in risk_items[:1 if is_light else 5])
    else:
        parts.append("- (non explicit)")

    if len(parts) > max_lines:
        parts = parts[:max_lines]

    return "\n".join(parts).strip() + "\n"


def write_pack_context(project_id: str, mode: Mode, content: str) -> Path:
    packs_dir = project_dir(project_id) / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = packs_dir / f"context_{mode}_{timestamp}.md"
    path.write_text(content, encoding="utf-8")
    return path
