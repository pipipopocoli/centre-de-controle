from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.data.model import AgentState


STALE_SECONDS = 10 * 60


def _format_age(seconds: float) -> str:
    if seconds < 30:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        rem = minutes % 60
        return f"{hours}h {rem}m ago" if rem else f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _format_heartbeat(heartbeat: str | None) -> tuple[str, bool]:
    if not heartbeat:
        return "Heartbeat: -", False
    try:
        ts = datetime.fromisoformat(heartbeat)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (now - ts).total_seconds()
        stale = delta > STALE_SECONDS
        delta = max(0.0, delta)
        return f"Heartbeat: {_format_age(delta)}", stale
    except ValueError:
        return f"Heartbeat: {heartbeat}", False


class AgentCard(QFrame):
    def __init__(self, state: AgentState) -> None:
        super().__init__()
        self.setObjectName("agentCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header: Name + Badge
        header = QHBoxLayout()
        name = QLabel(state.name)
        name.setObjectName("agentName")
        
        badge = QLabel(state.engine)
        badge.setObjectName("agentBadge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(50)  # Slightly wider for better padding

        header.addWidget(name)
        header.addStretch(1)
        header.addWidget(badge)

        # Info Row: Phase
        phase_row = QHBoxLayout()
        self.phase_label = QLabel(f"{state.phase}")
        self.phase_label.setObjectName("agentPhase")
        if state.status:
            color = "#0369a1" if state.status == "executing" else "#d1d5db"
            status_text = "En cours" if state.status == "executing" else "En attente"
            status_html = f"<span style='color:{color}; font-weight:bold;'>•</span> {status_text}"
            self.status_label = QLabel(status_html)
        else:
            self.status_label = QLabel("<span style='color:#d1d5db;'>•</span> En attente")
        
        self.status_label.setObjectName("agentStatus")
        
        phase_row.addWidget(self.phase_label)
        phase_row.addStretch(1)
        phase_row.addWidget(self.status_label)

        # Progress
        self.progress = QProgressBar()
        self.progress.setObjectName("agentProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(max(0, min(state.percent, 100)))
        # Text aligned center is default for some styles, but we can enforce if needed or leave to stylesheet
        
        # Footer: ETA + Heartbeat
        footer = QHBoxLayout()
        
        eta_text = "ETA: --" if state.eta_minutes is None else f"ETA: {state.eta_minutes}m"
        self.eta_label = QLabel(eta_text)
        self.eta_label.setObjectName("agentEta")
        
        heartbeat_text, stale = _format_heartbeat(state.heartbeat)
        self.heartbeat_label = QLabel(heartbeat_text)
        self.heartbeat_label.setObjectName("agentHeartbeat")
        self.heartbeat_label.setProperty("stale", stale)
        self.setProperty("stale", stale)

        footer.addWidget(self.eta_label)
        footer.addStretch(1)
        footer.addWidget(self.heartbeat_label)

        layout.addLayout(header)
        layout.addLayout(phase_row)
        layout.addWidget(self.progress)
        layout.addLayout(footer)


class AgentsGridWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("agentsGrid")
        self.setFrameShape(QFrame.StyledPanel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setSpacing(12)

        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll)

    def set_agents(self, agents: list[AgentState]) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        columns = 3
        for idx, agent in enumerate(agents):
            row = idx // columns
            col = idx % columns
            self.grid.addWidget(AgentCard(agent), row, col)

        if not agents:
            empty = QLabel("No agents yet")
            empty.setObjectName("agentsEmpty")
            self.grid.addWidget(empty, 0, 0)
