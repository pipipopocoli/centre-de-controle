from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt, Signal
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
WAITING_STATUSES = {"pinged", "queued", "dispatched", "reminded", "waiting_reconfirm"}
LEVEL_LABELS = {
    0: "L0 - Orchestration",
    1: "L1 - Leads",
    2: "L2 - Specialists",
    3: "Lx - Others",
}


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
        return "💤 Repos", "idle"
    normalized = status.strip().lower()
    if normalized in WAITING_STATUSES:
        return "⏳ Attente reponse", "waiting"
    mapping = {
        "idle": ("💤 Repos", "idle"),
        "planning": ("🧭 Planifie", "planning"),
        "executing": ("⚡ En action", "executing"),
        "verifying": ("🔎 Verification", "verifying"),
        "blocked": ("🔴 Bloque", "blocked"),
        "error": ("🔴 Erreur", "error"),
        "completed": ("✅ Termine", "completed"),
        "replied": ("💤 Repos", "idle"),
        "closed": ("💤 Repos", "idle"),
    }
    return mapping.get(normalized, (status, normalized))


def _status_bucket(state: AgentState) -> str:
    normalized = (state.status or "").strip().lower()
    blockers = [item.strip() for item in (state.blockers or []) if str(item).strip()]
    if blockers and normalized in {"", "idle", "completed", "replied", "closed"}:
        return "blocked"
    if normalized in {"blocked", "error"}:
        return "blocked"
    if normalized in {"planning", "executing", "verifying"}:
        return "action"
    if normalized in WAITING_STATUSES:
        return "waiting"
    return "rest"


class AgentCard(QFrame):
    context_selected = Signal(dict)

    def __init__(self, state: AgentState) -> None:
        super().__init__()
        self._state = state
        self.setObjectName("agentCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)

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
        engine_hint = "Engine: OpenRouter"
        badge.setToolTip(engine_hint)

        header.addWidget(name)
        header.addStretch(1)
        header.addWidget(badge)

        # Info Row: Phase + Status
        phase_row = QHBoxLayout()
        self.phase_label = QLabel(f"{state.phase}")
        self.phase_label.setObjectName("agentPhase")
        status_text, status_key = _status_label(state.status)

        blockers = [item.strip() for item in (state.blockers or []) if str(item).strip()]
        if blockers and status_key in {"idle", "completed"}:
            status_text = "🔴 Bloque (blockers)"
            status_key = "blocked"

        # Left-border stripe driven by QSS property
        self.setProperty("statusStripe", _status_bucket(state))

        self.status_label = QLabel(status_text)
        self.status_label.setObjectName("agentStatus")
        self.status_label.setProperty("status", status_key)
        self.status_label.setToolTip(f"Status: {status_text}")
        
        phase_row.addWidget(self.phase_label)
        phase_row.addStretch(1)
        phase_row.addWidget(self.status_label)

        # Task line
        self.task_header = QLabel("MISSION")
        self.task_header.setObjectName("agentTaskHeader")

        task_text = state.current_task.strip() if state.current_task else "-"
        self.task_label = QLabel(f"Tache: {task_text}")
        self.task_label.setObjectName("agentTask")
        self.task_label.setWordWrap(True)

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
        layout.addWidget(self.task_header)
        layout.addWidget(self.task_label)
        if blockers:
            blockers_header = QLabel("⚠ BLOCKERS")
            blockers_header.setObjectName("agentBlockersHeader")
            layout.addWidget(blockers_header)
            for blocker in blockers[:3]:
                blocker_label = QLabel(f"• {blocker}")
                blocker_label.setObjectName("agentBlocker")
                blocker_label.setWordWrap(True)
                layout.addWidget(blocker_label)
        layout.addWidget(self.progress)
        layout.addLayout(footer)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        payload = {
            "kind": "agent",
            "id": str(self._state.agent_id),
            "title": f"{self._state.name} ({self._state.phase})",
            "source_path": "",
            "source_uri": "",
        }
        self.context_selected.emit(payload)
        super().mousePressEvent(event)


class AgentsGridWidget(QFrame):
    context_selected = Signal(dict)

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
        grouped: dict[int, list[AgentState]] = {0: [], 1: [], 2: [], 3: []}
        for agent in agents:
            try:
                parsed_level = int(agent.level)
            except (TypeError, ValueError):
                parsed_level = 3
            level = parsed_level if parsed_level in {0, 1, 2} else 3
            grouped[level].append(agent)

        for level in grouped:
            grouped[level].sort(key=lambda item: (str(item.name or "").lower(), str(item.agent_id or "")))

        row_cursor = 0
        for level in [0, 1, 2, 3]:
            section_agents = grouped[level]
            if not section_agents:
                continue

            counts = {"action": 0, "waiting": 0, "blocked": 0, "rest": 0}
            for state in section_agents:
                counts[_status_bucket(state)] += 1

            section = QWidget()
            section_layout = QHBoxLayout(section)
            section_layout.setContentsMargins(2, 2, 2, 2)
            section_layout.setSpacing(8)

            header = QLabel(LEVEL_LABELS[level])
            header.setObjectName("agentLevelHeader")
            summary = QLabel(
                "action {action} | attente {waiting} | bloque {blocked} | repos {rest}".format(**counts)
            )
            summary.setObjectName("agentLevelSummary")

            section_layout.addWidget(header)
            section_layout.addStretch(1)
            section_layout.addWidget(summary)
            self.grid.addWidget(section, row_cursor, 0, 1, columns)
            row_cursor += 1

            for idx, agent in enumerate(section_agents):
                row = row_cursor + (idx // columns)
                col = idx % columns
                card = AgentCard(agent)
                card.context_selected.connect(self.context_selected.emit)
                self.grid.addWidget(card, row, col)

            row_cursor += (len(section_agents) + columns - 1) // columns

        if not agents:
            empty = QLabel("No agents yet")
            empty.setObjectName("agentsEmpty")
            self.grid.addWidget(empty, 0, 0)
