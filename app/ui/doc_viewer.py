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

ROOT_DIR = Path(__file__).resolve().parents[2]
ROADMAP_DOC_PATH = ROOT_DIR / "docs" / "cockpit_v2_roadmap.html"
TOURNAMENT_DOC_PATH = ROOT_DIR / "control" / "projects" / "cockpit" / "tournament-v1" / "TOURNAMENT_ARENA.html"


def _create_web_engine_view() -> tuple[QWidget | None, str]:
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except Exception:
        return None, "WebEngine unavailable. Read-only fallback active."
    try:
        return QWebEngineView(), "WebEngine active."
    except Exception:
        return None, "WebEngine init failed. Read-only fallback active."


class DocsViewerWidget(QFrame):
    DOC_SOURCES = {
        "roadmap": ROADMAP_DOC_PATH,
        "tournament": TOURNAMENT_DOC_PATH,
    }

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("docsViewer")
        self._current_doc_id = "roadmap"
        self._web_view, backend_status = _create_web_engine_view()
        self._backend_status = backend_status

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        toolbar = QWidget()
        toolbar.setObjectName("docsViewerToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        self._roadmap_btn = QPushButton("Roadmap")
        self._roadmap_btn.setObjectName("docsDocButton")
        self._roadmap_btn.clicked.connect(lambda: self.set_doc("roadmap"))
        toolbar_layout.addWidget(self._roadmap_btn)

        self._tournament_btn = QPushButton("Tournament")
        self._tournament_btn.setObjectName("docsDocButton")
        self._tournament_btn.clicked.connect(lambda: self.set_doc("tournament"))
        toolbar_layout.addWidget(self._tournament_btn)

        toolbar_layout.addStretch(1)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("docsActionButton")
        self._refresh_btn.clicked.connect(self.refresh_doc)
        toolbar_layout.addWidget(self._refresh_btn)

        self._open_btn = QPushButton("Open External")
        self._open_btn.setObjectName("docsActionButton")
        self._open_btn.clicked.connect(self._open_external)
        toolbar_layout.addWidget(self._open_btn)

        root.addWidget(toolbar)

        self._status = QLabel(self._backend_status)
        self._status.setObjectName("docsViewerStatus")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        if self._web_view is None:
            self._fallback = QTextBrowser()
            self._fallback.setObjectName("docsFallbackView")
            self._fallback.setReadOnly(True)
            self._fallback.setOpenExternalLinks(True)
            root.addWidget(self._fallback, 1)
        else:
            self._fallback = None
            root.addWidget(self._web_view, 1)

        self.refresh_doc()

    def current_doc_id(self) -> str:
        return self._current_doc_id

    def set_doc(self, doc_id: str) -> None:
        normalized = str(doc_id or "").strip().lower()
        if normalized not in self.DOC_SOURCES:
            return
        self._current_doc_id = normalized
        self.refresh_doc()

    def refresh_doc(self) -> None:
        path = self.DOC_SOURCES.get(self._current_doc_id, ROADMAP_DOC_PATH)
        self._roadmap_btn.setProperty("selected", self._current_doc_id == "roadmap")
        self._tournament_btn.setProperty("selected", self._current_doc_id == "tournament")
        self._roadmap_btn.style().polish(self._roadmap_btn)
        self._tournament_btn.style().polish(self._tournament_btn)

        if not path.exists():
            self._status.setText(f"{self._backend_status} | Missing doc file: {path}")
            if self._fallback is not None:
                self._fallback.setHtml(
                    "<h3>Document unavailable</h3>"
                    f"<p>Missing file:</p><p><code>{path}</code></p>"
                )
            return

        self._status.setText(f"{self._backend_status} | Document: {path}")
        if self._web_view is not None:
            self._web_view.setUrl(QUrl.fromLocalFile(str(path)))
            return

        file_url = path.resolve().as_uri()
        self._fallback.setHtml(
            "<h3>Read-only fallback</h3>"
            "<p>WebEngine is not available. Open the document externally or use a runtime with WebEngine.</p>"
            f"<p><a href='{file_url}'>{path.name}</a></p>"
            f"<p><code>{path}</code></p>"
        )

    def _open_external(self) -> None:
        path = self.DOC_SOURCES.get(self._current_doc_id, ROADMAP_DOC_PATH)
        if not path.exists():
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
