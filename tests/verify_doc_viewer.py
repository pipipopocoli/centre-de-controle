#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.data.store import load_project
from app.ui.doc_viewer import DocsViewerWidget
from app.ui.main_window import MainWindow


def _check_doc_sources_and_switch() -> None:
    widget = DocsViewerWidget()

    roadmap_path = DocsViewerWidget.DOC_SOURCES["roadmap"]
    tournament_path = DocsViewerWidget.DOC_SOURCES["tournament"]
    assert roadmap_path.exists(), f"roadmap doc missing: {roadmap_path}"
    assert tournament_path.exists(), f"tournament doc missing: {tournament_path}"

    assert widget.current_doc_id() == "roadmap", widget.current_doc_id()

    widget.set_doc("tournament")
    assert widget.current_doc_id() == "tournament", widget.current_doc_id()
    assert str(tournament_path) in widget._status.text(), widget._status.text()

    widget.set_doc("roadmap")
    assert widget.current_doc_id() == "roadmap", widget.current_doc_id()
    assert str(roadmap_path) in widget._status.text(), widget._status.text()

def _check_fallback_mode() -> None:
    with patch("app.ui.doc_viewer._create_web_engine_view", return_value=(None, "forced fallback for test")):
        widget = DocsViewerWidget()
        assert widget._web_view is None, "fallback widget must not have web view"
        assert widget._fallback is not None, "fallback text browser missing"
        assert "fallback" in widget._status.text().lower(), widget._status.text()
        widget.set_doc("tournament")
        html = widget._fallback.toHtml()
        assert "Read-only fallback" in html, "fallback explanation missing"
        assert "TOURNAMENT_ARENA.html" in html, "fallback should expose tournament document"


def _check_main_window_docs_tab() -> None:
    project = load_project("cockpit")

    with patch.object(MainWindow, "run_auto_mode_tick", lambda self: None):
        window = MainWindow(project=project, projects=[project.project_id])

    tab_labels = [window.center_tabs.tabText(i) for i in range(window.center_tabs.count())]
    assert "Docs" in tab_labels, tab_labels

    docs_index = tab_labels.index("Docs")
    QTest.mouseClick(window.sidebar.docs_btn, Qt.LeftButton)
    QApplication.processEvents()
    assert window.center_tabs.currentIndex() == docs_index


def main() -> int:
    app = QApplication.instance() or QApplication([])

    _check_doc_sources_and_switch()
    _check_fallback_mode()
    _check_main_window_docs_tab()

    app.quit()
    print("OK: doc viewer integration verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
