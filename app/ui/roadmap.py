from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class RoadmapWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("roadmap")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.timeline = QLabel("Timeline")
        self.timeline.setObjectName("roadmapTimeline")
        self.timeline.setFixedWidth(140)

        self.sections = QWidget()
        sections_layout = QHBoxLayout(self.sections)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(16)

        self.now = self._section("Now")
        self.next = self._section("Next")
        self.risks = self._section("Risks")

        sections_layout.addWidget(self.now)
        sections_layout.addWidget(self.next)
        sections_layout.addWidget(self.risks)

        layout.addWidget(self.timeline)
        layout.addWidget(self.sections, 1)

    def _section(self, title: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(title)
        label.setObjectName("roadmapSectionTitle")
        items = QLabel("-")
        items.setObjectName("roadmapSectionItems")
        items.setWordWrap(True)

        layout.addWidget(label)
        layout.addWidget(items)
        return box

    def set_roadmap(self, now: list[str], next_items: list[str], risks: list[str]) -> None:
        self.now.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in now) or "-")
        self.next.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in next_items) or "-")
        self.risks.findChild(QLabel, "roadmapSectionItems").setText("\n".join(f"- {item}" for item in risks) or "-")
