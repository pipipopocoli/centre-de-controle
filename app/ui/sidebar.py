from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget, QLabel


class SidebarWidget(QWidget):
    def __init__(self, projects: list[str] | None = None, footer_text: str | None = None) -> None:
        super().__init__()
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Projects")
        title.setObjectName("sidebarTitle")

        self.project_list = QListWidget()
        self.project_list.setObjectName("projectList")
        if projects:
            self.project_list.addItems(projects)

        self.project_list.setFocusPolicy(Qt.NoFocus)

        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setObjectName("newProjectButton")

        layout.addWidget(title)
        layout.addWidget(self.project_list, 1)

        if footer_text:
            self.version_label = QLabel(footer_text)
            self.version_label.setObjectName("versionStamp")
            self.version_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            layout.addWidget(self.version_label)
            
        layout.addWidget(self.new_project_btn)
