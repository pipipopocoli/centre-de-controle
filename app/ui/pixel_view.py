from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


INTENSITY_COLORS = {
    0: QColor("#111827"),
    1: QColor("#14532D"),
    2: QColor("#166534"),
    3: QColor("#15803D"),
}


class PixelViewWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pixelView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        self.window_selector = QComboBox()
        self.window_selector.addItem("24h", "24h")
        self.window_selector.addItem("7d", "7d")
        self.window_selector.addItem("30d", "30d")
        self.status_label = QLabel("No pixel feed yet")
        header_layout.addWidget(QLabel("Window"))
        header_layout.addWidget(self.window_selector)
        header_layout.addWidget(self.status_label, 1)

        self.grid = QTableWidget()
        self.grid.setObjectName("pixelGrid")
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.grid.setSelectionMode(QTableWidget.NoSelection)
        self.grid.verticalHeader().setVisible(True)
        self.grid.horizontalHeader().setVisible(True)

        layout.addWidget(header)
        layout.addWidget(self.grid, 1)

    def selected_window(self) -> str:
        return str(self.window_selector.currentData() or "24h")

    def set_feed(self, payload: dict[str, Any]) -> None:
        rows = payload.get("rows")
        if not isinstance(rows, list) or not rows:
            self.grid.clear()
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self.status_label.setText("No activity data")
            return
        first = rows[0] if isinstance(rows[0], dict) else {}
        cells = first.get("cells")
        columns = len(cells) if isinstance(cells, list) else 0
        self.grid.clear()
        self.grid.setRowCount(len(rows))
        self.grid.setColumnCount(columns)
        self.grid.setHorizontalHeaderLabels([str(index + 1) for index in range(columns)])
        self.grid.setVerticalHeaderLabels([str(item.get("agent_id") or f"agent-{idx}") for idx, item in enumerate(rows)])
        for row_index, row in enumerate(rows):
            row_cells = row.get("cells") if isinstance(row, dict) else []
            if not isinstance(row_cells, list):
                row_cells = []
            for col_index in range(columns):
                cell = row_cells[col_index] if col_index < len(row_cells) and isinstance(row_cells[col_index], dict) else {}
                intensity = int(cell.get("intensity") or 0)
                intensity = max(0, min(intensity, 3))
                item = QTableWidgetItem("")
                item.setBackground(INTENSITY_COLORS.get(intensity, INTENSITY_COLORS[0]))
                tooltip = (
                    f"bucket: {cell.get('bucket_start')}\n"
                    f"chat={cell.get('chat_messages', 0)}\n"
                    f"runs={cell.get('run_events', 0)}\n"
                    f"states={cell.get('state_updates', 0)}"
                )
                item.setToolTip(tooltip)
                self.grid.setItem(row_index, col_index, item)
        generated = str(payload.get("generated_at_utc") or "")
        window = str(payload.get("window") or self.selected_window())
        if generated:
            try:
                stamp = datetime.fromisoformat(generated.replace("Z", "+00:00")).strftime("%H:%M:%S")
            except ValueError:
                stamp = generated
            self.status_label.setText(f"{window} updated {stamp}")
        else:
            self.status_label.setText(f"{window} updated")

