from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
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
        self.global_list.setSpacing(6)
        self.global_list.addItem("Global feed ready")

        self.thread_selector = QComboBox()
        self.thread_selector.setObjectName("threadSelector")
        self.thread_selector.addItem("No threads", "")

        self.threads_list = QListWidget()
        self.threads_list.setObjectName("chatThreadList")
        self.threads_list.setSpacing(6)
        self.threads_list.addItem("No threads yet")

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
        # Compact buttons to avoid clipping (Paper Ops Fix)
        # ------------------------------------------------
        self.pack_light_btn = QPushButton("Pack (Light)")
        self.pack_light_btn.setToolTip("Pack Context (Light) - Summarized")
        self.pack_light_btn.setCursor(Qt.PointingHandCursor)
        
        self.pack_full_btn = QPushButton("Pack (Full)")
        self.pack_full_btn.setToolTip("Pack Context (Full) - All details")
        self.pack_full_btn.setCursor(Qt.PointingHandCursor)
        
        self.ping_btn = QPushButton("Ping Team")
        self.ping_btn.setToolTip("Ping Leo + Victor")
        self.ping_btn.setCursor(Qt.PointingHandCursor)
        # ------------------------------------------------
        
        actions.addWidget(self.pack_light_btn)
        actions.addWidget(self.pack_full_btn)
        actions.addWidget(self.ping_btn)

        layout.addWidget(title)
        layout.addWidget(self.tabs, 1)
        layout.addLayout(composer)
        layout.addLayout(actions)

    def _format_timestamp(self, timestamp: str) -> str:
        if not timestamp:
            return ""
        # Keep only time portion for readability.
        if "T" in timestamp:
            time_part = timestamp.split("T", 1)[1]
            return time_part.split("+", 1)[0].replace("Z", "")
        return timestamp

    def _author_color(self, author: str) -> QColor:
        key = author.lower().strip()
        if key == "operator":
            return QColor("#1E40AF")
        if key == "clems":
            return QColor("#6D28D9")
        if key == "system":
            return QColor("#374151")
        # default agent
        return QColor("#0F766E")

    def _author_badge(self, author: str) -> str:
        key = author.lower().strip()
        if key == "operator":
            return "OP"
        if key == "clems":
            return "CL"
        if key == "system":
            return "SYS"
        return "AG"

    def format_message(self, payload: dict) -> str:
        timestamp = self._format_timestamp(payload.get("timestamp", ""))
        author = payload.get("author", "operator")
        text = payload.get("text", "")
        badge = self._author_badge(author)
        if timestamp:
            return f"{timestamp} {badge} {author}: {text}"
        return f"{badge} {author}: {text}"

    def set_global_messages(self, messages: list[dict]) -> None:
        self.global_list.clear()
        if not messages:
            self.global_list.addItem("Global feed is empty")
            return
        from PySide6.QtWidgets import QListWidgetItem
        for payload in messages:
            text = self.format_message(payload)
            item = QListWidgetItem(text)
            item.setForeground(self._author_color(payload.get("author", "operator")))
            item.setToolTip(payload.get("timestamp", ""))
            self.global_list.addItem(item)

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
                index = tags.index(current)
                self.thread_selector.setCurrentIndex(index)
        self.thread_selector.blockSignals(False)

    def current_thread_tag(self) -> str:
        return self.thread_selector.currentData() or ""

    def set_thread_messages(self, messages: list[dict]) -> None:
        self.threads_list.clear()
        if not messages:
            self.threads_list.addItem("No thread messages")
            return
        for payload in messages:
            text = self.format_message(payload)
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(text)
            item.setForeground(self._author_color(payload.get("author", "operator")))
            item.setToolTip(payload.get("timestamp", ""))
            self.threads_list.addItem(item)
