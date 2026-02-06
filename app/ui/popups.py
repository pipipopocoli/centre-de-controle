from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


class PopupManager:
    def __init__(self, parent: QWidget | None = None) -> None:
        self.parent = parent

    def show_event(self, title: str, message: str) -> None:
        QMessageBox.information(self.parent, title, message)
