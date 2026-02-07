from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout


class AutoModePanel(QFrame):
    def __init__(self, data_dir: str = "") -> None:
        super().__init__()
        self.setObjectName("autoModePanel")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header + Toggle
        header_row = QHBoxLayout()
        header = QLabel("AUTO-MODE")
        header.setObjectName("autoModeHeader")
        
        self.toggle = QPushButton("OFF")
        self.toggle.setCheckable(True)
        self.toggle.setObjectName("autoModeToggle")
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setFixedWidth(60)
        self.toggle.toggled.connect(self._on_toggle)

        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(self.toggle)

        # Info
        self.dir_label = QLabel(f"Data: {data_dir or 'N/A'}")
        self.dir_label.setObjectName("autoModeInfo")
        self.dir_label.setWordWrap(True)
        
        self.microcopy = QLabel("Mentions -> inbox. Auto copie/ouvre 1 mission par cycle.")
        self.microcopy.setObjectName("autoModeMicrocopy")
        self.microcopy.setWordWrap(True)

        self.last_dispatch = QLabel("Last: -")
        self.last_dispatch.setObjectName("autoModeInfo")

        self.last_error = QLabel("")
        self.last_error.setObjectName("autoModeError")
        self.last_error.setWordWrap(True)

        self.run_once_btn = QPushButton("Run once")
        self.run_once_btn.setObjectName("autoModeRunOnce")
        self.run_once_btn.setCursor(Qt.PointingHandCursor)

        layout.addLayout(header_row)
        layout.addWidget(self.dir_label)
        layout.addWidget(self.microcopy)
        layout.addWidget(self.last_dispatch)
        layout.addWidget(self.last_error)
        layout.addWidget(self.run_once_btn)

    def _on_toggle(self, checked: bool) -> None:
        self.toggle.setText("ON" if checked else "OFF")

    def set_enabled(self, enabled: bool) -> None:
        self.toggle.blockSignals(True)
        self.toggle.setChecked(enabled)
        self.toggle.blockSignals(False)
        self.toggle.setText("ON" if enabled else "OFF")

    def is_enabled(self) -> bool:
        return bool(self.toggle.isChecked())

    def set_last_dispatch(self, text: str) -> None:
        self.last_dispatch.setText(f"Last: {text}")

    def set_last_error(self, text: str) -> None:
        self.last_error.setText(text)


class SidebarWidget(QWidget):
    def __init__(self, projects: list[str] | None = None, footer_text: str | None = None, data_dir: str = "") -> None:
        super().__init__()
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        title = QLabel("PROJECTS")
        title.setObjectName("sidebarTitle")

        self.project_list = QListWidget()
        self.project_list.setObjectName("projectList")
        if projects:
            self.project_list.addItems(projects)

        self.project_list.setFocusPolicy(Qt.NoFocus)

        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setObjectName("newProjectButton")

        # Auto-Mode Panel
        self.auto_mode = AutoModePanel(data_dir=data_dir)

        layout.addWidget(title)
        layout.addWidget(self.project_list, 1)
        layout.addWidget(self.auto_mode)
        layout.addWidget(self.new_project_btn)

        if footer_text:
            self.version_label = QLabel(footer_text)
            self.version_label.setObjectName("versionStamp")
            self.version_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            self.version_label.setWordWrap(True)
            layout.addWidget(self.version_label)
