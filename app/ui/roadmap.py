from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class RoadmapWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("roadmap")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)  # Spacing handled by separators

        # Create sections (FR Microcopy)
        # 1. MISSION (Phase + Objectif)
        self.mission = self._section("MISSION", "roadmapSectionMission")
        
        # 2. EN COURS (Now)
        self.focus = self._section("EN COURS", "roadmapSectionFocus")
        
        # 3. A VENIR (Next)
        self.upcoming = self._section("A VENIR", "roadmapSectionUpcoming")
        
        # 4. RISQUES
        self.risks = self._section("RISQUES", "roadmapSectionRisks")

        # Layout: Mission | En Cours | A Venir | Risques
        layout.addWidget(self.mission, 2)  # Give more space to mission
        layout.addWidget(self._separator())
        layout.addWidget(self.focus, 2)
        layout.addWidget(self._separator())
        layout.addWidget(self.upcoming, 2)
        layout.addWidget(self._separator())
        layout.addWidget(self.risks, 1)

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

    def set_state(self, phase: str, objective: str, next_items: list[str]) -> None:
        # Mission column combines Phase & Objective
        lines: list[str] = []
        if phase:
            lines.append(f"Phase: {phase}")
        if objective:
            lines.append(f"Cap: {objective}")
        
        self.mission.findChild(QLabel, "roadmapSectionItems").setText("\n".join(lines) or "-")
