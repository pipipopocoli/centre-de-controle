"""Visual timeline route widget - milestone route + chronological stream."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.services.timeline_feed import build_portfolio_timeline_feed, build_project_timeline_feed

# -------------------------------------------------------------------
# Palette
# -------------------------------------------------------------------
COLOR_DONE = QColor("#22C55E")
COLOR_ACTIVE = QColor("#2C5DFF")
COLOR_TODO = QColor("#C4C4C4")
COLOR_LINE = QColor("#1C1C1C")
COLOR_TEXT = QColor("#1C1C1C")
COLOR_DESC = QColor("#5E6167")
COLOR_BG = QColor("#F6F3EE")

DOT_RADIUS = 8
LINE_WIDTH = 3
ROW_HEIGHT = 70
LEFT_MARGIN = 40
TEXT_LEFT = LEFT_MARGIN + DOT_RADIUS + 18

LANE_FILTERS = {
    "all": "All",
    "risk": "Risks",
    "delivery": "Delivery",
    "runtime": "Runtime",
}


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

    issues_dir = project_dir / "issues"
    if issues_dir.exists():
        for path in sorted(issues_dir.glob("ISSUE-*.md")):
            info = _parse_issue_light(path)
            items.append(
                {
                    "label": info["title"],
                    "description": info.get("description", ""),
                    "status": info["status"],
                    "source": "issue",
                    "id": info["id"],
                }
            )

    state_path = project_dir / "STATE.md"
    state = _parse_state_items(state_path)

    for item in state.get("In Progress", []):
        if not any(it["label"].lower() in item.lower() for it in items):
            items.append(
                {
                    "label": item,
                    "description": "In Progress (STATE.md)",
                    "status": "active",
                    "source": "state",
                    "id": "",
                }
            )

    for item in state.get("Next", []):
        if not any(it["label"].lower() in item.lower() for it in items):
            items.append(
                {
                    "label": item,
                    "description": "Next (STATE.md)",
                    "status": "todo",
                    "source": "state",
                    "id": "",
                }
            )

    order = {"done": 0, "active": 1, "todo": 2}
    items.sort(key=lambda it: order.get(it["status"], 2))

    return items


class _TimelineCanvas(QWidget):
    """Custom-painted vertical timeline with dots and labels."""

    def __init__(self, items: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items = items
        self._mode = "simple"
        self._update_size()

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.update()

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

        pen = QPen(COLOR_LINE, LINE_WIDTH)
        painter.setPen(pen)
        painter.drawLine(LEFT_MARGIN, top_y, LEFT_MARGIN, bot_y)

        title_font = QFont("Inter", 13, QFont.DemiBold)
        desc_font = QFont("Inter", 11)
        id_font = QFont("Menlo", 9)

        for i, item in enumerate(self._items):
            cy = top_y + i * ROW_HEIGHT
            status = item.get("status", "todo")

            if status == "done":
                color = COLOR_DONE
            elif status == "active":
                color = COLOR_ACTIVE
            else:
                color = COLOR_TODO

            painter.setPen(Qt.NoPen)
            if status == "active":
                glow = QColor(COLOR_ACTIVE)
                glow.setAlpha(40)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(
                    LEFT_MARGIN - DOT_RADIUS - 4,
                    cy - DOT_RADIUS - 4,
                    (DOT_RADIUS + 4) * 2,
                    (DOT_RADIUS + 4) * 2,
                )

            if status == "todo":
                painter.setBrush(QBrush(COLOR_BG))
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(LEFT_MARGIN - DOT_RADIUS, cy - DOT_RADIUS, DOT_RADIUS * 2, DOT_RADIUS * 2)
            else:
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(LEFT_MARGIN - DOT_RADIUS, cy - DOT_RADIUS, DOT_RADIUS * 2, DOT_RADIUS * 2)

            painter.setPen(COLOR_TEXT)
            painter.setFont(title_font)
            label = str(item.get("label", ""))
            if len(label) > 60:
                label = label[:57] + "..."
            painter.drawText(TEXT_LEFT, cy + 5, label)

            desc = str(item.get("description", ""))
            if desc:
                painter.setPen(COLOR_DESC)
                painter.setFont(desc_font)
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                painter.drawText(TEXT_LEFT, cy + 22, desc)

                if len(desc) > 80:
                    desc = desc[:77] + "..."
                painter.drawText(TEXT_LEFT, cy + 22, desc)

            if self._mode == "tech" and item.get("id"):
                painter.setPen(COLOR_DESC)
                painter.setFont(id_font)
                painter.drawText(TEXT_LEFT, cy - 12, str(item.get("id")))

        painter.end()


class ProjectTimelineWidget(QFrame):
    """Scrollable timeline route showing milestones + chronological stream."""
    context_selected = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("projectTimeline")
        self._project: ProjectData | None = None
        self._portfolio: list[ProjectData] = []
        self._scope = "project"
        self._mode = "simple"
        self._lane_filter = "all"
        self._visible_events: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 0)
        header_layout.setSpacing(4)

        self._title = QLabel("Route du projet")
        self._title.setObjectName("timelineTitle")
        self._title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1C1C1C;")
        header_layout.addWidget(self._title)

        self._subtitle = QLabel("")
        self._subtitle.setObjectName("timelineSubtitle")
        self._subtitle.setStyleSheet("font-size: 12px; color: #5E6167;")
        header_layout.addWidget(self._subtitle)

        self._stats = QLabel("")
        self._stats.setObjectName("timelineStats")
        self._stats.setStyleSheet("font-size: 11px; color: #5E6167;")
        header_layout.addWidget(self._stats)
        root.addWidget(header)

        filter_bar = QWidget()
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(16, 0, 16, 0)
        filter_layout.setSpacing(6)
        filter_layout.addWidget(QLabel("Filter:"))

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        for key, label in LANE_FILTERS.items():
            button = QPushButton(label)
            button.setObjectName("timelineFilterButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, lane=key: self._set_lane_filter(lane))
            self._filter_group.addButton(button)
            filter_layout.addWidget(button)
            if key == "all":
                button.setChecked(True)
        filter_layout.addStretch(1)
        root.addWidget(filter_bar)

        route_frame = QFrame()
        route_frame.setObjectName("timelineRouteFrame")
        route_layout = QVBoxLayout(route_frame)
        route_layout.setContentsMargins(0, 0, 0, 0)
        route_layout.setSpacing(0)
        self._canvas = _TimelineCanvas([])
        self._scroll = QScrollArea()
        self._scroll.setWidget(self._canvas)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        route_layout.addWidget(self._scroll)
        root.addWidget(route_frame, 1)

        self._events = QTableWidget(0, 5)
        self._events.setObjectName("timelineEventsTable")
        self._events.setHorizontalHeaderLabels(["Time", "Lane", "Severity", "Event", "Source"])
        self._events.setAlternatingRowColors(True)
        self._events.setEditTriggers(QTableWidget.NoEditTriggers)
        self._events.setSelectionBehavior(QTableWidget.SelectRows)
        self._events.setSelectionMode(QTableWidget.SingleSelection)
        self._events.verticalHeader().setVisible(False)
        self._events.horizontalHeader().setStretchLastSection(True)
        self._events.setMinimumHeight(220)
        self._events.itemSelectionChanged.connect(self._on_event_selection_changed)
        root.addWidget(self._events, 1)

    def set_project(self, project: ProjectData) -> None:
        self._project = project
        self.refresh()

    def set_context(
        self,
        project: ProjectData,
        *,
        portfolio: list[ProjectData] | None = None,
        scope: str = "project",
        mode: str = "simple",
    ) -> None:
        self._project = project
        self._portfolio = list(portfolio or [])
        self._scope = "portfolio" if str(scope).strip().lower() == "portfolio" else "project"
        self._mode = "tech" if str(mode).strip().lower() == "tech" else "simple"
        self.refresh()

    def set_mode(self, mode: str) -> None:
        self._mode = "tech" if str(mode).strip().lower() == "tech" else "simple"
        self.refresh()

    def set_scope(self, scope: str, *, portfolio: list[ProjectData] | None = None) -> None:
        self._scope = "portfolio" if str(scope).strip().lower() == "portfolio" else "project"
        if portfolio is not None:
            self._portfolio = list(portfolio)
        self.refresh()

    def _set_lane_filter(self, lane: str) -> None:
        if lane not in LANE_FILTERS:
            lane = "all"
        self._lane_filter = lane
        self.refresh()

    def _filtered_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self._lane_filter == "all":
            return events
        if self._lane_filter == "risk":
            return [item for item in events if str(item.get("lane") or "") == "risk"]
        return [item for item in events if str(item.get("lane") or "") == self._lane_filter]

    def _fill_table(self, events: list[dict[str, Any]]) -> None:
        rows = events[:50] if self._mode == "tech" else events[:16]
        self._visible_events = rows
        show_source = self._mode == "tech"
        columns = 5 if show_source else 4
        self._events.clear()
        if show_source:
            self._events.setColumnCount(5)
            self._events.setHorizontalHeaderLabels(["Time", "Lane", "Severity", "Event", "Source"])
        else:
            self._events.setColumnCount(4)
            self._events.setHorizontalHeaderLabels(["Time", "Lane", "Severity", "Event"])
        self._events.setRowCount(len(rows))

        for row_idx, event in enumerate(rows):
            time_value = str(event.get("ts_iso") or "")[11:19] if "T" in str(event.get("ts_iso") or "") else str(event.get("ts_iso") or "")
            lane = str(event.get("lane") or "-")
            severity = str(event.get("severity") or "info")
            title = str(event.get("title") or "event")
            details = str(event.get("details") or "")
            source = str(event.get("source_path") or "")

            event_text = title if self._mode == "simple" else f"{title} | {details}"
            values = [time_value, lane, severity, event_text]
            if show_source:
                values.append(source)

            for col_idx in range(columns):
                cell = QTableWidgetItem(values[col_idx])
                if severity == "critical":
                    cell.setForeground(QColor("#B91C1C"))
                    cell.setFont(QFont("Inter", 11, QFont.Bold))
                elif severity == "warn":
                    cell.setForeground(QColor("#B45309"))  # Amber-700 for better visibility
                    cell.setFont(QFont("Inter", 11, QFont.DemiBold))
                self._events.setItem(row_idx, col_idx, cell)

        self._events.resizeColumnsToContents()

    def _on_event_selection_changed(self) -> None:
        row = self._events.currentRow()
        if row < 0 or row >= len(self._visible_events):
            return
        event = self._visible_events[row]
        title = str(event.get("title") or "timeline event")
        source_path = str(event.get("source_path") or "")
        source_uri = str(event.get("source_uri") or "")
        context_kind = "timeline"
        context_id = str(event.get("event_id") or f"timeline-{row}")

        issue_match = re.search(r"(ISSUE-[A-Za-z0-9-]+)", title, re.IGNORECASE)
        if issue_match:
            context_kind = "issue"
            context_id = issue_match.group(1).upper()

        payload = {
            "kind": context_kind,
            "id": context_id,
            "title": title,
            "source_path": source_path,
            "source_uri": source_uri,
            "selected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        self.context_selected.emit(payload)

    def refresh(self) -> None:
        if self._project is None:
            return

        milestone_items = build_timeline_items(self._project)
        self._canvas.set_items(milestone_items)
        self._canvas.set_mode(self._mode)

        done = sum(1 for it in milestone_items if it.get("status") == "done")
        active = sum(1 for it in milestone_items if it.get("status") == "active")
        total = len(milestone_items)

        if self._scope == "portfolio" and self._portfolio:
            feed = build_portfolio_timeline_feed(self._portfolio, limit=220)
            title_scope = "portfolio"
        else:
            feed = build_project_timeline_feed(self._project, limit=160)
            title_scope = "project"

        events = feed.get("events") if isinstance(feed.get("events"), list) else []
        filtered = self._filtered_events([item for item in events if isinstance(item, dict)])
        self._fill_table(filtered)

        stats = feed.get("stats") if isinstance(feed.get("stats"), dict) else {}
        by_lane = stats.get("by_lane") if isinstance(stats.get("by_lane"), dict) else {}
        by_severity = stats.get("by_severity") if isinstance(stats.get("by_severity"), dict) else {}
        stats_text = (
            f"events={int(stats.get('events_total', 0))} "
            f"| delivery={int(by_lane.get('delivery', 0))} "
            f"runtime={int(by_lane.get('runtime', 0))} "
            f"risk={int(by_lane.get('risk', 0))} "
            f"| critical={int(by_severity.get('critical', 0))}"
        )

        self._title.setText(f"Route - {self._project.name}")
        self._subtitle.setText(
            f"{done} done | {active} active | {max(total - done - active, 0)} upcoming | {total} total | scope={title_scope} mode={self._mode}"
        )
        self._stats.setText(stats_text)
