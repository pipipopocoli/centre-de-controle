from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt, QTimer
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
        self._global_keys: list[str] = []
        self._thread_keys: list[str] = []
        self._thread_scope_tag: str = ""
        self._current_context_ref: dict | None = None

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
        self.input.setPlaceholderText("Message... (#tag, @leo, @victor, @nova, @clems, @agent-1)")
        self.send_btn = QPushButton("Send")

        composer.addWidget(self.input)
        composer.addWidget(self.send_btn)

        context_row = QHBoxLayout()
        self.context_badge = QLabel("Context: none")
        self.context_badge.setObjectName("chatContextBadge")
        self.context_badge.setToolTip("Click timeline/agent/state items to attach context to next message.")
        self.context_clear_btn = QPushButton("Clear context")
        self.context_clear_btn.setObjectName("chatContextClearButton")
        self.context_clear_btn.clicked.connect(self.clear_context_ref)
        self.context_clear_btn.setEnabled(False)
        context_row.addWidget(self.context_badge, 1)
        context_row.addWidget(self.context_clear_btn)

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
        self.ping_btn.setToolTip("Ping Leo + Victor + Nova")
        self.ping_btn.setCursor(Qt.PointingHandCursor)
        # ------------------------------------------------
        
        actions.addWidget(self.pack_light_btn)
        actions.addWidget(self.pack_full_btn)
        actions.addWidget(self.ping_btn)

        layout.addWidget(title)
        layout.addWidget(self.tabs, 1)
        layout.addLayout(composer)
        layout.addLayout(context_row)
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
        context_ref = payload.get("context_ref")
        context_suffix = ""
        if isinstance(context_ref, dict):
            title = str(context_ref.get("title") or "").strip()
            if title:
                context_suffix = f" [ctx: {title}]"
        if timestamp:
            return f"{timestamp} {badge} {author}: {text}{context_suffix}"
        return f"{badge} {author}: {text}{context_suffix}"

    def _message_key(self, payload: dict, index_hint: int) -> str:
        message_id = str(payload.get("message_id") or "").strip()
        if message_id:
            return message_id
        ts = str(payload.get("timestamp") or "")
        author = str(payload.get("author") or "")
        text = str(payload.get("text") or "")
        return f"{ts}|{author}|{text}|{index_hint}"

    def _capture_scroll_state(self, widget: QListWidget) -> tuple[int, bool]:
        bar = widget.verticalScrollBar()
        value = bar.value()
        at_bottom = (bar.maximum() - value) <= 4
        return value, at_bottom

    def _restore_scroll_state(self, widget: QListWidget, previous_value: int, at_bottom: bool, rebuilt: bool = False) -> None:
        if at_bottom:
            # Always stick to bottom if user was already there
            widget.scrollToBottom()
            return
            
        if not rebuilt:
            # Incremental append: Qt handles this perfectly. Do not touch the viewport.
            return
            
        # Rebuild happened: defer restoration so Qt layout finishes calculating sizes
        def do_restore():
            bar = widget.verticalScrollBar()
            bar.setValue(min(previous_value, bar.maximum()))
        
        QTimer.singleShot(0, do_restore)

    def _render_list_item(self, payload: dict) -> "QListWidgetItem":
        from PySide6.QtWidgets import QListWidgetItem

        text = self.format_message(payload)
        item = QListWidgetItem(text)
        item.setForeground(self._author_color(payload.get("author", "operator")))
        item.setToolTip(payload.get("timestamp", ""))
        return item

    def _should_rebuild(self, existing: list[str], incoming: list[str]) -> bool:
        if not existing:
            return True
        if len(incoming) < len(existing):
            return True
        for idx, key in enumerate(existing):
            if incoming[idx] != key:
                return True
        return False

    def set_global_messages(self, messages: list[dict]) -> None:
        previous_value, at_bottom = self._capture_scroll_state(self.global_list)
        if not messages:
            self.global_list.clear()
            self.global_list.addItem("Global feed is empty")
            self._global_keys = []
            return
        incoming_keys = [self._message_key(payload, idx) for idx, payload in enumerate(messages)]
        rebuilt = self._should_rebuild(self._global_keys, incoming_keys)
        
        if rebuilt:
            self.global_list.clear()
            for payload in messages:
                self.global_list.addItem(self._render_list_item(payload))
        else:
            for payload in messages[len(self._global_keys) :]:
                self.global_list.addItem(self._render_list_item(payload))
                
        self._global_keys = incoming_keys
        self._restore_scroll_state(self.global_list, previous_value, at_bottom, rebuilt=rebuilt)

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

    def set_thread_messages(self, messages: list[dict], *, thread_tag: str = "") -> None:
        normalized_tag = str(thread_tag or "").strip().lower()
        thread_changed = normalized_tag != self._thread_scope_tag
        previous_value, at_bottom = self._capture_scroll_state(self.threads_list)
        if thread_changed:
            self._thread_keys = []
            self._thread_scope_tag = normalized_tag
            self.threads_list.clear()
        if not messages:
            self.threads_list.clear()
            self.threads_list.addItem("No thread messages")
            self._thread_keys = []
            return
        incoming_keys = [self._message_key(payload, idx) for idx, payload in enumerate(messages)]
        rebuilt = thread_changed or self._should_rebuild(self._thread_keys, incoming_keys)
        
        if rebuilt:
            self.threads_list.clear()
            for payload in messages:
                self.threads_list.addItem(self._render_list_item(payload))
        else:
            for payload in messages[len(self._thread_keys) :]:
                self.threads_list.addItem(self._render_list_item(payload))
                
        self._thread_keys = incoming_keys
        self._restore_scroll_state(self.threads_list, previous_value, at_bottom, rebuilt=rebuilt)

    def set_context_ref(self, context_ref: dict | None) -> None:
        if not isinstance(context_ref, dict):
            self._current_context_ref = None
            self.context_badge.setText("Context: none")
            self.context_badge.setToolTip("Click timeline/agent/state items to attach context to next message.")
            self.context_clear_btn.setEnabled(False)
            return

        title = str(context_ref.get("title") or "").strip() or "selected"
        selected_at = str(context_ref.get("selected_at") or "")
        kind = str(context_ref.get("kind") or "context")
        self._current_context_ref = dict(context_ref)
        self.context_badge.setText(f"Context: {title}")
        self.context_badge.setToolTip(f"{kind} | {selected_at}" if selected_at else kind)
        self.context_clear_btn.setEnabled(True)

    def clear_context_ref(self) -> None:
        self.set_context_ref(None)

    def current_context_ref(self) -> dict | None:
        if not isinstance(self._current_context_ref, dict):
            return None
        return dict(self._current_context_ref)

    def consume_context_ref(self) -> dict | None:
        current = self.current_context_ref()
        self.clear_context_ref()
        return current

    def reset_feed_state(self) -> None:
        self._global_keys = []
        self._thread_keys = []
        self._thread_scope_tag = ""
        self.global_list.clear()
        self.threads_list.clear()
        self.global_list.addItem("Global feed ready")
        self.threads_list.addItem("No threads yet")
