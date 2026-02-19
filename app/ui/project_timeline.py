"""Visual timeline route widget — vertical line with milestone dots.

Parses project issues and STATE.md to build a visual "route" showing
completed (green), active (blue), and upcoming (gray) milestones.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData

# -------------------------------------------------------------------
# Palette
# -------------------------------------------------------------------
COLOR_DONE = QColor("#22C55E")       # green
COLOR_ACTIVE = QColor("#2C5DFF")     # blue
COLOR_TODO = QColor("#C4C4C4")       # gray
COLOR_LINE = QColor("#1C1C1C")       # black line
COLOR_TEXT = QColor("#1C1C1C")
COLOR_DESC = QColor("#5E6167")
COLOR_BG = QColor("#F6F3EE")

DOT_RADIUS = 8
LINE_WIDTH = 3
ROW_HEIGHT = 70
LEFT_MARGIN = 40
TEXT_LEFT = LEFT_MARGIN + DOT_RADIUS + 18


# -------------------------------------------------------------------
# Data helpers
# -------------------------------------------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _normalize_status(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"done", "completed", "closed", "merged"}:
        return "done"
    if value in {"in progress", "in_progress", "executing", "active", "wip"}:
        return "active"
    return "todo"


def _parse_issue_light(path: Path) -> dict[str, str]:
    """Extract id, title, status from an issue markdown file."""
    data: dict[str, str] = {"id": path.stem, "title": path.stem, "status": "todo", "description": ""}
    lines = _read_text(path).splitlines()
    if lines and lines[0].startswith("# "):
        header = lines[0][2:].strip()
        if " - " in header:
            issue_id, title = header.split(" - ", 1)
            data["id"] = issue_id.strip()
            data["title"] = title.strip()
        else:
            data["title"] = header

    for raw in lines:
        line = raw.strip()
        if line.startswith("- Status:"):
            data["status"] = _normalize_status(line.split(":", 1)[1])
        if line.startswith("- Phase:"):
            data["description"] = f"Phase: {line.split(':', 1)[1].strip()}"
    return data


def _parse_state_items(path: Path) -> dict[str, list[str]]:
    """Extract Now/Next/Blockers from STATE.md."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current and line.startswith("- "):
            item = line[2:].strip()
            if item.lower() not in {"none", "n/a", "-"}:
                sections[current].append(item)
    return sections


def build_timeline_items(project: ProjectData) -> list[dict[str, Any]]:
    """Build ordered list of timeline milestones from project data."""
    project_dir = project.path
    items: list[dict[str, Any]] = []

    # 1. Parse issues
    issues_dir = project_dir / "issues"
    if issues_dir.exists():
        for path in sorted(issues_dir.glob("ISSUE-*.md")):
            info = _parse_issue_light(path)
            items.append({
                "label": info["title"],
                "description": info.get("description", ""),
                "status": info["status"],
                "source": "issue",
                "id": info["id"],
            })

    # 2. Add Now items from STATE.md as active
    state_path = project_dir / "STATE.md"
    state = _parse_state_items(state_path)

    for item in state.get("In Progress", []):
        # Avoid duplicating issues already listed
        if not any(it["label"].lower() in item.lower() for it in items):
            items.append({
                "label": item,
                "description": "In Progress (STATE.md)",
                "status": "active",
                "source": "state",
                "id": "",
            })

    for item in state.get("Next", []):
        if not any(it["label"].lower() in item.lower() for it in items):
            items.append({
                "label": item,
                "description": "Next (STATE.md)",
                "status": "todo",
                "source": "state",
                "id": "",
            })

    # Sort: done first, then active, then todo
    order = {"done": 0, "active": 1, "todo": 2}
    items.sort(key=lambda it: order.get(it["status"], 2))

    return items


# -------------------------------------------------------------------
# Canvas widget — draws the line + dots via QPainter
# -------------------------------------------------------------------
class _TimelineCanvas(QWidget):
    """Custom-painted vertical timeline with dots and labels."""

    def __init__(self, items: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items = items
        self._update_size()

    def set_items(self, items: list[dict[str, Any]]) -> None:
        self._items = items
        self._update_size()
        self.update()

    def _update_size(self) -> None:
        height = max(200, len(self._items) * ROW_HEIGHT + 40)
        self.setFixedHeight(height)
        self.setMinimumWidth(400)

    def paintEvent(self, event: Any) -> None:  # noqa: N802
        if not self._items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        n = len(self._items)
        top_y = 28
        bot_y = top_y + (n - 1) * ROW_HEIGHT

        # --- Draw vertical line ---
        pen = QPen(COLOR_LINE, LINE_WIDTH)
        painter.setPen(pen)
        painter.drawLine(LEFT_MARGIN, top_y, LEFT_MARGIN, bot_y)

        # --- Draw each milestone ---
        title_font = QFont("Inter", 13, QFont.DemiBold)
        desc_font = QFont("Inter", 11)
        id_font = QFont("Menlo", 9)

        for i, item in enumerate(self._items):
            cy = top_y + i * ROW_HEIGHT
            status = item.get("status", "todo")

            # Pick color
            if status == "done":
                color = COLOR_DONE
            elif status == "active":
                color = COLOR_ACTIVE
            else:
                color = COLOR_TODO

            # Draw dot
            painter.setPen(Qt.NoPen)
            if status == "active":
                # Glow ring
                glow = QColor(COLOR_ACTIVE)
                glow.setAlpha(40)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(LEFT_MARGIN - DOT_RADIUS - 4, cy - DOT_RADIUS - 4,
                                    (DOT_RADIUS + 4) * 2, (DOT_RADIUS + 4) * 2)

            if status == "todo":
                # Hollow circle
                painter.setBrush(QBrush(COLOR_BG))
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(LEFT_MARGIN - DOT_RADIUS, cy - DOT_RADIUS,
                                    DOT_RADIUS * 2, DOT_RADIUS * 2)
            else:
                # Filled circle
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(LEFT_MARGIN - DOT_RADIUS, cy - DOT_RADIUS,
                                    DOT_RADIUS * 2, DOT_RADIUS * 2)

            # --- Title text ---
            painter.setPen(COLOR_TEXT)
            painter.setFont(title_font)
            label = item.get("label", "")
            # Truncate if needed
            if len(label) > 60:
                label = label[:57] + "..."
            painter.drawText(TEXT_LEFT, cy + 5, label)

            # --- Description text ---
            desc = item.get("description", "")
            if desc:
                painter.setPen(COLOR_DESC)
                painter.setFont(desc_font)
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                painter.drawText(TEXT_LEFT, cy + 22, desc)

            # --- Status badge ---
            if item.get("id"):
                painter.setPen(COLOR_DESC)
                painter.setFont(id_font)
                painter.drawText(TEXT_LEFT, cy - 12, item["id"])

        painter.end()


# -------------------------------------------------------------------
# Public widget
# -------------------------------------------------------------------
class ProjectTimelineWidget(QFrame):
    """Scrollable timeline route showing project milestones."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("projectTimeline")
        self._project: ProjectData | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 8)

        self._title = QLabel("Route du projet")
        self._title.setObjectName("timelineTitle")
        self._title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1C1C1C;")
        header_layout.addWidget(self._title)

        self._subtitle = QLabel("")
        self._subtitle.setObjectName("timelineSubtitle")
        self._subtitle.setStyleSheet("font-size: 12px; color: #5E6167;")
        header_layout.addWidget(self._subtitle)

        root.addWidget(header)

        # Scrollable canvas
        self._canvas = _TimelineCanvas([])
        scroll = QScrollArea()
        scroll.setWidget(self._canvas)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

    def set_project(self, project: ProjectData) -> None:
        self._project = project
        self.refresh()

    def refresh(self) -> None:
        if self._project is None:
            return

        items = build_timeline_items(self._project)
        self._canvas.set_items(items)

        done = sum(1 for it in items if it["status"] == "done")
        active = sum(1 for it in items if it["status"] == "active")
        total = len(items)

        self._title.setText(f"Route — {self._project.name}")
        self._subtitle.setText(
            f"{done} fait  ·  {active} en cours  ·  {total - done - active} à venir  ·  {total} total"
        )
