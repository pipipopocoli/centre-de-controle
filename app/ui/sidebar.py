import re
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
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


class RuntimeContextPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("runtimeContextPanel")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.project_title = QLabel("Project: -")
        self.project_title.setObjectName("runtimeContextTitle")
        self.project_title.setWordWrap(True)

        self.project_warning = QLabel("")
        self.project_warning.setObjectName("projectMismatch")
        self.project_warning.setWordWrap(True)
        self.project_warning.setVisible(False)

        self.mode_badge = QLabel("Mode: -")
        self.mode_badge.setObjectName("runtimeModeBadge")
        self.mode_badge.setWordWrap(True)

        self.app_stamp = QLabel("App stamp: -")
        self.app_stamp.setObjectName("runtimeContextLine")
        self.app_stamp.setWordWrap(True)

        self.repo_head = QLabel("Repo head: -")
        self.repo_head.setObjectName("runtimeContextLine")
        self.repo_head.setWordWrap(True)

        self.project_context = QLabel("Project context: -")
        self.project_context.setObjectName("runtimeContextLine")
        self.project_context.setWordWrap(True)

        self.info_line = QLabel("stamp:- | head:-")
        self.info_line.setObjectName("runtimeContextLine")
        self.info_line.setWordWrap(True)

        self.runtime_root = QLabel("Runtime root: -")
        self.runtime_root.setObjectName("runtimeContextLine")
        self.runtime_root.setWordWrap(True)

        self.live_scope = QLabel("Live scope: -")
        self.live_scope.setObjectName("runtimeLiveScope")
        self.live_scope.setWordWrap(True)

        self.warning = QLabel("")
        self.warning.setObjectName("runtimeMismatch")
        self.warning.setWordWrap(True)
        self.warning.setVisible(False)

        self.rebuild_button = QPushButton("Rebuild app")
        self.rebuild_button.setObjectName("rebuildAppButton")
        self.rebuild_button.setCursor(Qt.PointingHandCursor)
        self.rebuild_button.clicked.connect(self._open_packaging_guide)

        layout.addWidget(self.project_title)
        layout.addWidget(self.project_warning)
        layout.addWidget(self.mode_badge)
        layout.addWidget(self.app_stamp)
        layout.addWidget(self.repo_head)
        layout.addWidget(self.project_context)
        layout.addWidget(self.info_line)
        layout.addWidget(self.runtime_root)
        layout.addWidget(self.live_scope)
        layout.addWidget(self.warning)
        layout.addWidget(self.rebuild_button)

    def _extract_sha(self, value: str) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.endswith("*"):
            raw = raw[:-1]
        if "@" in raw:
            raw = raw.rsplit("@", 1)[-1]
        match = re.search(r"\b[0-9a-fA-F]{7,40}\b", raw)
        return match.group(0).lower() if match else ""

    def set_context(
        self,
        app_stamp: str,
        repo_head: str,
        project_id: str,
        *,
        runtime_mode: str = "",
        runtime_source: str = "",
        runtime_root: str = "",
    ) -> None:
        app_value = str(app_stamp or "").strip() or "-"
        repo_value = str(repo_head or "").strip() or "-"
        project_value = str(project_id or "").strip() or "-"
        mode_value = str(runtime_mode or "").strip().upper() or "DEV LIVE"
        source_value = str(runtime_source or "").strip().lower() or "unknown"
        root_value = str(runtime_root or "").strip() or "-"
        source_label_map = {
            "repo": "repo",
            "appsupport": "appsupport",
            "custom": "custom",
            "unknown": "unknown",
        }
        source_label = source_label_map.get(source_value, source_value)

        is_canonical = project_value.lower() == "cockpit"

        if is_canonical:
            self.project_title.setText(f"🔒 {project_value} (Canonical)")
            self.project_title.setProperty("canonical", "true")
            self.project_warning.setText("")
            self.project_warning.setVisible(False)
        else:
            self.project_title.setText(f"⚠️ {project_value} (Non-canonical)")
            self.project_title.setProperty("canonical", "false")
            self.project_warning.setText(
                "Warning: You are viewing an archived or non-canonical project. "
                "Runtime truth and pilotage actions may not reflect the active Cockpit state."
            )
            self.project_warning.setVisible(True)

        self.project_title.style().polish(self.project_title)
        self.mode_badge.setText(f"Mode: {mode_value}")
        self.app_stamp.setText(f"App stamp: {app_value}")
        self.repo_head.setText(f"Repo head: {repo_value}")
        self.project_context.setText(f"Project context: {project_value}")
        self.info_line.setText(f"stamp:{app_value} | head:{repo_value}")
        self.runtime_root.setText(f"Runtime root [{source_label}]: {root_value}")
        if mode_value == "RELEASE":
            self.live_scope.setText(
                "Live scope: runtime data only; rebuild to ship new code/UI. "
                "Single app icon expected in release mode."
            )
        else:
            self.live_scope.setText(
                "Live scope: data + QSS now; restart app for Python code changes. "
                "Dev Live may show 2 dock icons (launcher + python rocket) and this is expected."
            )

        app_sha = self._extract_sha(app_value)
        repo_sha = self._extract_sha(repo_value)
        mismatch = bool(app_sha and repo_sha and app_sha != repo_sha)
        if mismatch:
            self.warning.setText(f"Build mismatch: running {app_value}, repo {repo_value}")
            self.warning.setVisible(True)
        else:
            self.warning.setText("")
            self.warning.setVisible(False)

    def _open_packaging_guide(self) -> None:
        guide_path = Path(__file__).resolve().parents[2] / "docs" / "PACKAGING.md"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(guide_path)))


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
        self.runtime_context = RuntimeContextPanel()
        self.auto_mode = AutoModePanel(data_dir=data_dir)

        layout.addWidget(self.runtime_context)
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

    def set_runtime_context(
        self,
        app_stamp: str,
        repo_head: str,
        project_id: str,
        *,
        runtime_mode: str = "",
        runtime_source: str = "",
        runtime_root: str = "",
    ) -> None:
        self.runtime_context.set_context(
            app_stamp,
            repo_head,
            project_id,
            runtime_mode=runtime_mode,
            runtime_source=runtime_source,
            runtime_root=runtime_root,
        )
