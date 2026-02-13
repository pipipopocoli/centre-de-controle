from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

PHASES = ["Plan", "Implement", "Test", "Review", "Ship"]
PHASE_DISPLAY = {
    "Plan": "CONCEPTION",
    "Implement": "CODE",
    "Test": "TEST",
    "Review": "VALIDATION",
    "Ship": "DEPLOIEMENT",
}
PHASE_ALIASES = {label: key for key, label in PHASE_DISPLAY.items()}
PHASE_ALIASES.update(
    {
        "CONCEPTION": "Plan",
        "CODE": "Implement",
        "TEST": "Test",
        "VALIDATION": "Review",
        "DEPLOIEMENT": "Ship",
    }
)


def normalize_phase_key(phase: str) -> str:
    value = (phase or "").strip()
    lowered = value.lower()
    if lowered in {"plan", "planning"}:
        return "Plan"
    if lowered in {"implement", "implementation", "code"}:
        return "Implement"
    if lowered in {"test", "qa", "testing"}:
        return "Test"
    if lowered in {"review", "validation", "verify", "verifying"}:
        return "Review"
    if lowered in {"ship", "release", "deploiement", "deploy"}:
        return "Ship"
    return PHASE_ALIASES.get(value, value)


def phase_display_label(phase: str) -> str:
    key = normalize_phase_key(phase)
    return PHASE_DISPLAY.get(key, key)


class RoadmapWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("roadmap")
        self.setFrameShape(QFrame.StyledPanel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # Timeline row (phase tracker + ETA)
        self.phase_labels: list[QLabel] = []
        self.phase_keys: list[str] = []
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(10)

        for phase in PHASES:
            label = QLabel(phase_display_label(phase))
            label.setObjectName("phaseStep")
            label.setProperty("active", False)
            label.setCursor(Qt.PointingHandCursor)
            label.setToolTip(f"Phase: {phase}")
            self.phase_labels.append(label)
            self.phase_keys.append(phase)
            timeline_row.addWidget(label)

        timeline_row.addStretch(1)
        self.phase_eta = QLabel("ETA: --")
        self.phase_eta.setObjectName("phaseEta")
        timeline_row.addWidget(self.phase_eta)

        outer.addLayout(timeline_row)

        # Create sections (FR microcopy)
        # 1. CAP (Etape + Cible)
        self.mission = self._section("CAP", "roadmapSectionMission")

        # 2. FOCUS (Now)
        self.focus = self._section("FOCUS", "roadmapSectionFocus")

        # 3. SUITE (Next)
        self.upcoming = self._section("SUITE", "roadmapSectionUpcoming")

        # 4. ALERTES (Risks)
        self.risks = self._section("ALERTES", "roadmapSectionRisks")

        # Layout: Mission | En Cours | A Venir | Risques
        sections_row = QHBoxLayout()
        sections_row.setSpacing(0)
        sections_row.addWidget(self.mission, 2)
        sections_row.addWidget(self._separator())
        sections_row.addWidget(self.focus, 2)
        sections_row.addWidget(self._separator())
        sections_row.addWidget(self.upcoming, 2)
        sections_row.addWidget(self._separator())
        sections_row.addWidget(self.risks, 1)
        outer.addLayout(sections_row)

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
        line.setObjectName("roadmapSeparator")
        return line

    def _section(self, title: str, object_name: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        # Header with indicator
        header = QLabel(f"● {title}")
        header.setObjectName(object_name)
        
        # Content list
        items = QLabel("-")
        items.setObjectName("roadmapSectionItems")
        items.setWordWrap(True)
        items.setAlignment(Qt.AlignTop)

        layout.addWidget(header)
        layout.addWidget(items, 1) # Push content up
        return box

    def set_roadmap(self, now: list[str], next_items: list[str], risks: list[str]) -> None:
        self.focus.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in now) or "-")
        self.upcoming.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in next_items) or "-")
        self.risks.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in risks) or "-")

    def set_state(self, phase: str, objective: str, next_items: list[str], eta: str | None = None) -> None:
        # Cap column combines Etape & Cible
        lines: list[str] = []
        if phase:
            lines.append(f"Etape: {phase_display_label(phase)}")
        if objective:
            lines.append(f"Cible: {objective}")
        
        self.mission.findChild(QLabel, "roadmapSectionItems").setText("\n".join(lines) or "-")

        # Phase tracker
        active_phase = normalize_phase_key(phase)
        for key, label in zip(self.phase_keys, self.phase_labels):
            label.setProperty("active", key == active_phase)
            label.style().unpolish(label)
            label.style().polish(label)

        if eta:
            self.phase_eta.setText(f"ETA: {eta}")
        else:
            self.phase_eta.setText("ETA: --")
