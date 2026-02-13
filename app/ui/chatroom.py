from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ChatroomWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("chatroom")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Chatroom")
        title.setObjectName("chatroomTitle")

        self.tabs = QTabWidget()
        self.tabs.setObjectName("chatroomTabs")

        self.global_list = QListWidget()
        self.global_list.setObjectName("chatGlobalList")
        self.global_list.setWordWrap(True)
        self.global_list.setSpacing(8)

        self.thread_selector = QComboBox()
        self.thread_selector.setObjectName("threadSelector")
        self.thread_selector.addItem("No threads", "")

        self.threads_list = QListWidget()
        self.threads_list.setObjectName("chatThreadList")
        self.threads_list.setWordWrap(True)
        self.threads_list.setSpacing(8)

        global_tab = QWidget()
        global_layout = QVBoxLayout(global_tab)
        global_layout.setContentsMargins(0, 0, 0, 0)
        global_layout.addWidget(self.global_list)

        threads_tab = QWidget()
        threads_layout = QVBoxLayout(threads_tab)
        threads_layout.setContentsMargins(0, 0, 0, 0)
        threads_layout.setSpacing(8)
        threads_layout.addWidget(self.thread_selector)
        threads_layout.addWidget(self.threads_list)

        self.tabs.addTab(global_tab, "Global")
        self.tabs.addTab(threads_tab, "Threads")

        composer = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Message... (#tag, @leo, @victor, @clems, @agent-1)")
        self.send_btn = QPushButton("Send")
        composer.addWidget(self.input)
        composer.addWidget(self.send_btn)

        actions = QHBoxLayout()
        self.pack_light_btn = QPushButton("Pack (Light)")
        self.pack_light_btn.setToolTip("Pack Context (Light) - Summarized")
        self.pack_light_btn.setCursor(Qt.PointingHandCursor)

        self.pack_full_btn = QPushButton("Pack (Full)")
        self.pack_full_btn.setToolTip("Pack Context (Full) - All details")
        self.pack_full_btn.setCursor(Qt.PointingHandCursor)

        self.ping_btn = QPushButton("Ping Team")
        self.ping_btn.setToolTip("Ping Leo + Victor")
        self.ping_btn.setCursor(Qt.PointingHandCursor)

        actions.addWidget(self.pack_light_btn)
        actions.addWidget(self.pack_full_btn)
        actions.addWidget(self.ping_btn)

        layout.addWidget(title)
        layout.addWidget(self.tabs, 1)
        layout.addLayout(composer)
        layout.addLayout(actions)

    def _parse_ts(self, timestamp: str) -> datetime | None:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _format_time(self, timestamp: str) -> str:
        parsed = self._parse_ts(timestamp)
        if parsed is None:
            return ""
        return parsed.strftime("%H:%M")

    def _badge(self, author: str) -> str:
        lowered = author.lower().strip()
        if lowered == "operator":
            return "OP"
        if lowered == "clems":
            return "CL"
        if lowered == "system":
            return "SYS"
        return "AG"

    def _author_color(self, author: str) -> QColor:
        lowered = author.lower().strip()
        if lowered == "operator":
            return QColor("#1E40AF")
        if lowered == "clems":
            return QColor("#6D28D9")
        if lowered == "system":
            return QColor("#374151")
        return QColor("#0F766E")

    def _capture_scroll_state(self, target_list: QListWidget) -> dict[str, object]:
        bar = target_list.verticalScrollBar()
        top_item = target_list.itemAt(5, 5)
        top_id = top_item.data(Qt.UserRole) if top_item else None
        return {
            "at_bottom": bar.value() >= (bar.maximum() - 5),
            "top_id": top_id,
            "value": bar.value(),
            "max": bar.maximum(),
        }

    def _restore_scroll_state(self, target_list: QListWidget, state: dict[str, object]) -> None:
        bar = target_list.verticalScrollBar()
        if bool(state.get("at_bottom")):
            bar.setValue(bar.maximum())
            return

        top_id = state.get("top_id")
        if top_id:
            for idx in range(target_list.count()):
                item = target_list.item(idx)
                if item.data(Qt.UserRole) == top_id:
                    target_list.scrollToItem(item, QListWidget.PositionAtTop)
                    return

        old_max = int(state.get("max") or 0)
        if old_max <= 0:
            return
        ratio = float(state.get("value") or 0) / float(old_max)
        bar.setValue(int(ratio * max(bar.maximum(), 0)))

    def _render_items(self, target_list: QListWidget, messages: list[dict]) -> None:
        target_list.clear()
        if not messages:
            target_list.addItem("No messages")
            return

        prev_author = ""
        prev_ts: datetime | None = None

        for payload in messages:
            author = str(payload.get("author", "operator"))
            text = str(payload.get("text", ""))
            ts_raw = str(payload.get("timestamp", ""))
            ts = self._parse_ts(ts_raw)
            group = False
            if prev_author == author and prev_ts and ts and (ts - prev_ts) <= timedelta(minutes=2):
                group = True

            if group:
                content = text
            else:
                header = f"{self._format_time(ts_raw)} {self._badge(author)} {author.upper()}".strip()
                content = f"{header}\n{text}"

            item = QListWidgetItem(content)
            item.setForeground(self._author_color(author))
            item.setToolTip(ts_raw)
            item.setData(Qt.UserRole, payload.get("message_id") or ts_raw or content)
            target_list.addItem(item)

            prev_author = author
            prev_ts = ts

    def set_global_messages(self, messages: list[dict]) -> None:
        scroll_state = self._capture_scroll_state(self.global_list)
        self._render_items(self.global_list, messages)
        self._restore_scroll_state(self.global_list, scroll_state)

    def set_thread_tags(self, tags: list[str]) -> None:
        current = self.thread_selector.currentData()
        self.thread_selector.blockSignals(True)
        self.thread_selector.clear()
        if not tags:
            self.thread_selector.addItem("No threads", "")
            self.thread_selector.setEnabled(False)
        else:
            self.thread_selector.setEnabled(True)
            for tag in tags:
                self.thread_selector.addItem(f"#{tag}", tag)
            if current in tags:
                self.thread_selector.setCurrentIndex(tags.index(current))
        self.thread_selector.blockSignals(False)

    def current_thread_tag(self) -> str:
        return self.thread_selector.currentData() or ""

    def set_thread_messages(self, messages: list[dict]) -> None:
        scroll_state = self._capture_scroll_state(self.threads_list)
        self._render_items(self.threads_list, messages)
        self._restore_scroll_state(self.threads_list, scroll_state)
