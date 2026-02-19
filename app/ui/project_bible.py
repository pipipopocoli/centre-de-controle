from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.services.project_bible import (
    build_project_bible_html,
    resolve_linked_repo_path,
    update_vulgarisation,
)


class ProjectBibleWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("projectBible")
        self._project: ProjectData | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.title_label = QLabel("Vulgarisation")
        self.title_label.setObjectName("projectBibleTitle")
        header_layout.addWidget(self.title_label, 1)

        self.open_project_btn = QPushButton("Open Project Folder")
        self.open_project_btn.setObjectName("bibleActionButton")
        self.open_project_btn.clicked.connect(self._open_project_folder)
        header_layout.addWidget(self.open_project_btn)

        self.open_repo_btn = QPushButton("Open Linked Repo")
        self.open_repo_btn.setObjectName("bibleActionButton")
        self.open_repo_btn.clicked.connect(self._open_repo_folder)
        header_layout.addWidget(self.open_repo_btn)

        self.refresh_btn = QPushButton("Update Vulgarisation")
        self.refresh_btn.setObjectName("bibleActionButton")
        self.refresh_btn.clicked.connect(self.refresh_content)
        header_layout.addWidget(self.refresh_btn)

        root.addWidget(header)

        self.view = QTextBrowser()
        self.view.setObjectName("projectBibleView")
        self.view.setOpenExternalLinks(True)
        self.view.setReadOnly(True)
        self.view.setHtml("<p>Load a project to view its vulgarisation output.</p>")
        root.addWidget(self.view, 1)

    def set_project(self, project: ProjectData, *, refresh: bool = False) -> None:
        previous_id = self._project.project_id if self._project is not None else ""
        self._project = project
        self.title_label.setText(f"Vulgarisation - {project.name}")
        if refresh or previous_id != project.project_id:
            self.refresh_content()

    def refresh_content(self) -> None:
        if self._project is None:
            self.view.setHtml("<p>No active project.</p>")
            return
        try:
            result = update_vulgarisation(self._project)
        except Exception as exc:  # noqa: BLE001
            self.view.setHtml(
                "<h2>Vulgarisation</h2>"
                "<p>Could not build vulgarisation content.</p>"
                f"<p><code>{str(exc)}</code></p>"
            )
            return
        url = QUrl.fromLocalFile(str(result.html_path))
        self.view.setSource(url)
        if self.view.toPlainText().strip():
            return
        # Fallback path in case QTextBrowser cannot load local source.
        self.view.setHtml(build_project_bible_html(self._project))

    def _open_project_folder(self) -> None:
        if self._project is None:
            return
        path = self._project.path
        if not path.exists():
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_repo_folder(self) -> None:
        if self._project is None:
            return
        repo_path = resolve_linked_repo_path(self._project.settings)
        if repo_path is None:
            return
        if not Path(repo_path).exists():
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(repo_path)))
