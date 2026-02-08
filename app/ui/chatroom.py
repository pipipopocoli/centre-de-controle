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
from datetime import datetime, timedelta, timezone


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
        self.global_list.setSpacing(12)
        self.global_list.addItem("Global feed ready")

        self.thread_selector = QComboBox()
        self.thread_selector.setObjectName("threadSelector")
        self.thread_selector.addItem("No threads", "")

        self.threads_list = QListWidget()
        self.threads_list.setObjectName("chatThreadList")
        self.threads_list.setSpacing(12)
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
        # Keep only time portion (HH:MM) for readability.
        if "T" in timestamp:
            time_part = timestamp.split("T", 1)[1]
            # time_part is HH:MM:SS.ssss+00:00 -> split + -> take HH:MM
            return time_part.split("+", 1)[0].rsplit(":", 1)[0]
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

    def _parse_ts(self, timestamp: str) -> datetime | None:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _render_items(self, target_list: QListWidget, messages: list[dict]) -> None:
        target_list.clear()
        if not messages:
            target_list.addItem("No messages")
            return

        from PySide6.QtWidgets import QListWidgetItem
        from datetime import datetime, timedelta
        
        prev_author = None
        prev_time = None
        
        for payload in messages:
            author = payload.get("author", "operator")
            text = payload.get("text", "")
            ts_str = payload.get("timestamp", "")
            ts = self._parse_ts(ts_str)
            
            is_grouped = False
            if prev_author == author and prev_time and ts:
                delta = ts - prev_time
                if delta < timedelta(minutes=2):
                    is_grouped = True

            # Format
            # We use a crude text formatting for QListWidget items for now.
            # Ideally this would be QListWidgetItem + setItemWidget(custom_widget)
            # But to keep it simple and robust:
            
            display_text = text
            if not is_grouped:
                # Header
                badge = self._author_badge(author)
                time_str = ts.strftime("%H:%M") if ts else ""
                header = f"{badge}  {author.upper()}  {time_str}"
                display_text = f"{header}\n{text}"
            
            item = QListWidgetItem(display_text)
            color = self._author_color(author)
            
            # If formatted with header, maybe style differently?
            # For now just set color.
            # If grouped, maybe dim specific parts? Hard with plain text item.
            # We'll rely on the newline spacing.
            
            item.setForeground(color)
            item.setToolTip(ts_str)
            target_list.addItem(item)
            
            prev_author = author
            prev_time = ts

    def _capture_scroll_state(self, target_list: QListWidget) -> dict:
        bar = target_list.verticalScrollBar()
        is_at_bottom = bar.value() >= (bar.maximum() - 5)
        
        # Find top visible item to anchor to
        top_item_text = ""
        # We can't easily get the 'top item' from QListWidget without iteration or coordinate checks
        # But we can check itemAt(0, 0) relative to viewport?
        # A simpler approach for now: save the timestamp of the first visible item?
        # QListWidget doesn't expose "first visible item" easily.
        # Let's stick to is_at_bottom for the primary use case (chat).
        # For history viewing, ratio is 'okay' but specific item is better.
        
        # improved strategy: use itemAt(x, y) with viewport coordinates
        top_item = target_list.itemAt(5, 5)
        top_ts = None
        if top_item:
            # We stored timestamp in toolTip as a hack in the previous code.
            # We will continue to store it in UserRole or ToolTip.
            top_ts = top_item.data(Qt.UserRole) 

        return {
            "is_at_bottom": is_at_bottom,
            "top_ts": top_ts,
            "val": bar.value(),
            "max": bar.maximum()
        }

    def _restore_scroll_state(self, target_list: QListWidget, state: dict) -> None:
        bar = target_list.verticalScrollBar()
        
        if state.get("is_at_bottom"):
            bar.setValue(bar.maximum())
            return

        # Try to restore by timestamp
        target_ts = state.get("top_ts")
        if target_ts:
            for i in range(target_list.count()):
                item = target_list.item(i)
                if item.data(Qt.UserRole) == target_ts:
                    target_list.scrollToItem(item, QListWidget.PositionAtTop)
                    # Adjust slightly if needed, but PositionAtTop is usually good.
                    return

        # Fallback to ratio if exact item not found (e.g. deleted)
        if state["max"] > 0:
            ratio = state["val"] / state["max"]
            target_value = int(ratio * bar.maximum())
            bar.setValue(target_value)

    def _render_items(self, target_list: QListWidget, messages: list[dict]) -> None:
        target_list.clear()
        
        if not messages:
            return

        prev_author = None
        prev_time = None

        for payload in messages:
            author = payload.get("author", "operator")
            text = payload.get("text", "")
            ts_str = payload.get("timestamp", "")
            ts = self._parse_ts(ts_str)

            # Grouping logic
            is_grouped = False
            if prev_author == author and prev_time and ts:
                delta = ts - prev_time
                if delta < timedelta(minutes=2):
                    is_grouped = True
            
            # --- Create Custom Widget ---
            widget = QWidget()
            widget_layout = QVBoxLayout(widget)
            widget_layout.setContentsMargins(4, 2, 4, 2)
            widget_layout.setSpacing(2)

            # Header (only if not grouped)
            if not is_grouped:
                header_layout = QHBoxLayout()
                header_layout.setSpacing(6)
                header_layout.setContentsMargins(0, 4, 0, 0) # Top padding for new group

                badge_text = self._author_badge(author)
                badge_label = QLabel(badge_text)
                badge_label.setObjectName("chatBadge")
                # We can style chatBadge in css
                badge_label.setStyleSheet(f"""
                    background-color: {self._author_color(author).name()}; 
                    color: white; 
                    border-radius: 4px; 
                    padding: 2px 6px; 
                    font-size: 10px; 
                    font-weight: bold;
                """)
                
                author_label = QLabel(author.upper())
                author_label.setStyleSheet("font-weight: bold; color: #4B5563; font-size: 12px;")
                
                time_str = ts.strftime("%H:%M") if ts else ""
                time_label = QLabel(time_str)
                time_label.setStyleSheet("color: #9CA3AF; font-size: 10px;")

                header_layout.addWidget(badge_label)
                header_layout.addWidget(author_label)
                header_layout.addWidget(time_label)
                header_layout.addStretch()
                
                widget_layout.addLayout(header_layout)

            # Message Body
            msg_label = QLabel(text)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("""
                QLabel {
                    color: #1F2937;
                    font-size: 13px;
                    line-height: 1.4;
                    padding-left: 36px; /* Indent to align with text above if desired, or 0 if pure block */
                }
            """)
            if not is_grouped:
                 msg_label.setStyleSheet("""
                    QLabel {
                        color: #1F2937;
                        font-size: 13px;
                        line-height: 1.4;
                        padding-left: 0px; 
                    }
                """)

            widget_layout.addWidget(msg_label)
            
            # Item Sizing
            target_list.setResizeMode(QListWidget.Adjust) 
            
            item = QListWidgetItem(target_list)
            # define UserRole data for scroll anchoring
            item.setData(Qt.UserRole, ts_str)
            
            target_list.setItemWidget(item, widget)
            # Important: setSizeHint is needed for smooth scrolling if items vary significantly, 
            # but usually widget size hint is enough. 
            # item.setSizeHint(widget.sizeHint()) # Can't do this reliably before show.

            prev_author = author
            prev_time = ts

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
                index = tags.index(current)
                self.thread_selector.setCurrentIndex(index)
        self.thread_selector.blockSignals(False)

    def current_thread_tag(self) -> str:
        return self.thread_selector.currentData() or ""

    def set_thread_messages(self, messages: list[dict]) -> None:
        scroll_state = self._capture_scroll_state(self.threads_list)
        self._render_items(self.threads_list, messages)
        self._restore_scroll_state(self.threads_list, scroll_state)

