"""Pilotage tab — clear operational dashboard with visual timeline.

Replaces the dense HTML view with native Qt widgets:
- Phase header with progress bar
- Now / Next / Blockers columns
- Visual timeline route (issues + state)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.ui.project_timeline import ProjectTimelineWidget, _parse_state_items

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


PHASE_PROGRESS = {
    "plan": 10,
    "planning": 10,
    "implement": 25,
    "implementation": 25,
    "code": 25,
    "test": 50,
    "testing": 50,
    "qa": 50,
    "review": 75,
    "validation": 75,
    "verify": 75,
    "ship": 90,
    "deploy": 90,
    "deploiement": 90,
    "release": 95,
    "done": 100,
}


def _phase_percent(phase: str) -> int:
    return PHASE_PROGRESS.get(phase.strip().lower(), 10)


# -------------------------------------------------------------------
# List column widget (Now / Next / Blockers)
# -------------------------------------------------------------------
class _InfoColumn(QFrame):
    def __init__(self, title: str, emoji: str, color: str) -> None:
        super().__init__()
        self.setObjectName("pilotageInfoColumn")
        self.setStyleSheet(f"""
            QFrame#pilotageInfoColumn {{
                background: #FFFFFF;
                border: 1px solid #D9D3C8;
                border-radius: 8px;
                border-top: 3px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QLabel(f"{emoji} {title}")
        header.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {color};")
        layout.addWidget(header)

        self._list = QLabel("—")
        self._list.setObjectName("pilotageColumnList")
        self._list.setWordWrap(True)
        self._list.setAlignment(Qt.AlignTop)
        self._list.setStyleSheet("font-size: 12px; color: #1C1C1C; line-height: 1.5;")
        layout.addWidget(self._list, 1)

    def set_items(self, items: list[str]) -> None:
        if not items:
            self._list.setText("Aucun")
            return
        lines = []
        for item in items[:8]:
            text = item.strip()
            if len(text) > 120:
                text = text[:117] + "..."
            lines.append(f"• {text}")
        self._list.setText("\n".join(lines))


# -------------------------------------------------------------------
# Main widget
# -------------------------------------------------------------------
class ProjectPilotageWidget(QFrame):
    project_selected = Signal(str)
    mode_changed = Signal(str)
    scope_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("projectPilotage")
        self._project: ProjectData | None = None
        self._portfolio: list[ProjectData] = []
        self._mode = "simple"
        self._scope = "project"
        self._portfolio_throttle_seconds = 10
        self._portfolio_cache_html = ""
        self._portfolio_cache_at: datetime | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # ── Header bar ──────────────────────────────────────────────
        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(8)

        self._title = QLabel("Pilotage")
        self._title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1C1C1C;")
        h_lay.addWidget(self._title, 1)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setObjectName("pilotageActionButton")
        self.refresh_btn.clicked.connect(lambda: self.refresh_content(force=True))
        h_lay.addWidget(self.refresh_btn)

        self.mode_btn = QPushButton("Mode: Simple")
        self.mode_btn.setObjectName("pilotageActionButton")
        self.mode_btn.clicked.connect(self._toggle_mode)
        h_lay.addWidget(self.mode_btn)

        self.scope_btn = QPushButton("Scope: Projet")
        self.scope_btn.setObjectName("pilotageActionButton")
        self.scope_btn.clicked.connect(self._toggle_scope)
        h_lay.addWidget(self.scope_btn)

        self.auto_badge = QLabel("Auto 5s")
        self.auto_badge.setObjectName("pilotageModeBadge")
        h_lay.addWidget(self.auto_badge)

        root.addWidget(header)

        # ── Phase bar ───────────────────────────────────────────────
        phase_frame = QFrame()
        phase_frame.setObjectName("pilotagePhaseFrame")
        phase_frame.setStyleSheet("""
            QFrame#pilotagePhaseFrame {
                background: #FFFFFF;
                border: 1px solid #D9D3C8;
                border-radius: 8px;
            }
        """)
        phase_lay = QVBoxLayout(phase_frame)
        phase_lay.setContentsMargins(14, 10, 14, 10)
        phase_lay.setSpacing(6)

        phase_row = QHBoxLayout()
        self._phase_label = QLabel("Phase: —")
        self._phase_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #2C5DFF;")
        phase_row.addWidget(self._phase_label)
        phase_row.addStretch(1)
        self._phase_pct = QLabel("")
        self._phase_pct.setStyleSheet("font-size: 12px; color: #5E6167; font-family: Menlo, monospace;")
        phase_row.addWidget(self._phase_pct)
        phase_lay.addLayout(phase_row)

        self._objective_label = QLabel("")
        self._objective_label.setWordWrap(True)
        self._objective_label.setStyleSheet("font-size: 12px; color: #5E6167;")
        phase_lay.addWidget(self._objective_label)

        self._progress = QProgressBar()
        self._progress.setObjectName("pilotageProgress")
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar { background: #E8E2D9; border: none; border-radius: 4px; }
            QProgressBar::chunk { background: #2C5DFF; border-radius: 4px; }
        """)
        phase_lay.addWidget(self._progress)

        root.addWidget(phase_frame)

        # ── Now / Next / Blockers ───────────────────────────────────
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(10)
        self._col_now = _InfoColumn("Maintenant", "⚡", "#2C5DFF")
        self._col_next = _InfoColumn("Prochain", "➡️", "#0F766E")
        self._col_blockers = _InfoColumn("Blockers", "🚧", "#C94B4B")
        cols_layout.addWidget(self._col_now, 1)
        cols_layout.addWidget(self._col_next, 1)
        cols_layout.addWidget(self._col_blockers, 1)
        root.addLayout(cols_layout)

        # ── Timeline route ──────────────────────────────────────────
        self._timeline = ProjectTimelineWidget()
        root.addWidget(self._timeline, 1)

    # ── Public API (keep backward compat with MainWindow) ──────────
    @property
    def mode(self) -> str:
        return self._mode

    @property
    def scope(self) -> str:
        return self._scope

    def set_throttle_seconds(self, seconds: int) -> None:
        try:
            value = int(seconds)
        except (TypeError, ValueError):
            value = 10
        self._portfolio_throttle_seconds = max(1, min(value, 120))

    def set_project(self, project: ProjectData, portfolio: list[ProjectData], *, refresh: bool = False) -> None:
        previous_id = self._project.project_id if self._project is not None else ""
        self._project = project
        self._portfolio = list(portfolio)
        self._title.setText(f"Pilotage — {project.name}")

        if previous_id != project.project_id:
            self._portfolio_cache_html = ""
            self._portfolio_cache_at = None

        if refresh or previous_id != project.project_id:
            self.refresh_content(force=True)

    def set_mode(self, mode: str, *, emit_signal: bool = False) -> None:
        normalized = str(mode or "simple").strip().lower()
        if normalized not in {"simple", "tech"}:
            normalized = "simple"
        if self._mode == normalized:
            self._update_mode_label()
            return
        self._mode = normalized
        self._update_mode_label()
        if emit_signal:
            self.mode_changed.emit(self._mode)
        self.refresh_content(force=True)

    def set_scope(self, scope: str, *, emit_signal: bool = False) -> None:
        normalized = str(scope or "project").strip().lower()
        if normalized not in {"project", "portfolio"}:
            normalized = "project"
        if self._scope == normalized:
            self._update_scope_label()
            return
        self._scope = normalized
        self._update_scope_label()
        if emit_signal:
            self.scope_changed.emit(self._scope)
        self.refresh_content(force=True)

    def refresh_content(self, *, force: bool = False) -> None:
        if self._project is None:
            return

        project_dir = self._project.path
        state_path = project_dir / "STATE.md"
        state = _parse_state_items(state_path)

        # Phase
        phase_items = state.get("Phase", [])
        phase = phase_items[0] if phase_items else "Plan"
        pct = _phase_percent(phase)
        self._phase_label.setText(f"Phase: {phase}")
        self._phase_pct.setText(f"{pct}%")
        self._progress.setValue(pct)

        # Objective
        obj_items = state.get("Objective", [])
        obj = obj_items[0] if obj_items else ""
        self._objective_label.setText(f"Cible: {obj}" if obj else "")

        # Now / Next / Blockers
        self._col_now.set_items(state.get("Now", []) + state.get("In Progress", []))
        self._col_next.set_items(state.get("Next", []))
        self._col_blockers.set_items(state.get("Blockers", []))

        # Timeline
        self._timeline.set_project(self._project)

    def _toggle_mode(self) -> None:
        next_mode = "tech" if self._mode == "simple" else "simple"
        self.set_mode(next_mode, emit_signal=True)

    def _toggle_scope(self) -> None:
        next_scope = "portfolio" if self._scope == "project" else "project"
        self.set_scope(next_scope, emit_signal=True)

    def _update_mode_label(self) -> None:
        label = "Simple" if self._mode == "simple" else "Tech"
        self.mode_btn.setText(f"Mode: {label}")

    def _update_scope_label(self) -> None:
        label = "Projet" if self._scope == "project" else "Portefeuille"
        self.scope_btn.setText(f"Scope: {label}")
