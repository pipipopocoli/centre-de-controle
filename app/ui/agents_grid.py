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
        return "Last update: -", False
    try:
        ts = datetime.fromisoformat(heartbeat)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (now - ts).total_seconds()
        stale = delta > STALE_SECONDS
        delta = max(0.0, delta)
        return f"Last update: {_format_age(delta)}", stale
    except ValueError:
        return f"Last update: {heartbeat}", False


def _status_label(status: str | None) -> tuple[str, str]:
    if not status:
        return "En attente", "idle"
    normalized = status.strip().lower()
    mapping = {
        "idle": ("En attente", "idle"),
        "planning": ("Planifie", "planning"),
        "executing": ("En cours", "executing"),
        "pinged": ("Ping envoye", "pinged"),
        "queued": ("En file", "planning"),
        "dispatched": ("Distribue", "executing"),
        "reminded": ("Rappel", "verifying"),
        "replied": ("Repondu", "completed"),
        "verifying": ("Verification", "verifying"),
        "blocked": ("Bloque", "blocked"),
        "error": ("Erreur", "error"),
        "completed": ("Termine", "completed"),
    }
    return mapping.get(normalized, (status, normalized))


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
        engine_hint = "Engine: Codex" if state.engine == "CDX" else "Engine: Antigravity"
        badge.setToolTip(engine_hint)

        header.addWidget(name)
        header.addStretch(1)
        header.addWidget(badge)

        # Info Row: Phase + Status
        phase_row = QHBoxLayout()
        self.phase_label = QLabel(f"{state.phase}")
        self.phase_label.setObjectName("agentPhase")
        status_text, status_key = _status_label(state.status)
        self.status_label = QLabel(status_text)
        self.status_label.setObjectName("agentStatus")
        self.status_label.setProperty("status", status_key)
        self.status_label.setToolTip(f"Status: {status_text}")
        
        phase_row.addWidget(self.phase_label)
        phase_row.addStretch(1)
        phase_row.addWidget(self.status_label)

        # Task line
        task_text = state.current_task.strip() if state.current_task else "-"
        self.task_label = QLabel(f"Mission: {task_text}")
        self.task_label.setObjectName("agentTask")
        self.task_label.setWordWrap(True)
        self.task_label.setProperty("active", status_key in {"executing", "planning", "verifying", "pinged"})

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
        self.heartbeat_label.setToolTip("Last update from agent")
        self.setProperty("stale", stale)

        footer.addWidget(self.eta_label)
        footer.addStretch(1)
        footer.addWidget(self.heartbeat_label)

        layout.addLayout(header)
        layout.addLayout(phase_row)
        layout.addWidget(self.task_label)
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
        grouped: dict[int, list[AgentState]] = {0: [], 1: [], 2: []}
        for agent in agents:
            level = agent.level if isinstance(agent.level, int) else 2
            if level not in grouped:
                level = 2
            grouped[level].append(agent)

        section_titles = {
            0: "L0 - Orchestration",
            1: "L1 - Leads",
            2: "L2 - Specialists",
        }

        row = 0
        for level in (0, 1, 2):
            section_agents = sorted(grouped.get(level, []), key=lambda a: a.name.lower())
            if not section_agents:
                continue

            header = QLabel(section_titles[level])
            header.setObjectName("agentsGroupHeader")
            self.grid.addWidget(header, row, 0, 1, columns)
            row += 1

            col = 0
            for agent in section_agents:
                self.grid.addWidget(AgentCard(agent), row, col)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1
            if col != 0:
                row += 1

        if not agents:
            empty = QLabel("No agents yet")
            empty.setObjectName("agentsEmpty")
            self.grid.addWidget(empty, 0, 0)
