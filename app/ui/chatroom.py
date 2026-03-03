from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# ── Colour palette ────────────────────────────────────────────────────
COLORS = {
    "operator_bg": "#1E3A5F",
    "operator_text": "#E8F0FE",
    "agent_bg": "#1E293B",
    "agent_text": "#CBD5E1",
    "system_bg": "#0F172A",
    "system_text": "#64748B",
    "clems_bg": "#312E81",
    "clems_text": "#C7D2FE",
    "typing_bg": "#1E1B4B",
    "typing_text": "#818CF8",
    "timestamp": "#475569",
    "badge_operator": "#3B82F6",
    "badge_clems": "#7C3AED",
    "badge_system": "#374151",
    "badge_agent": "#0D9488",
    "input_bg": "#0F172A",
    "input_border": "#1E293B",
    "input_text": "#E2E8F0",
    "send_bg": "#6366F1",
    "send_hover": "#818CF8",
    "send_text": "#FFFFFF",
}


def _badge_color(author: str) -> str:
    key = author.lower().strip()
    if key == "operator":
        return COLORS["badge_operator"]
    if key == "clems":
        return COLORS["badge_clems"]
    if key == "system":
        return COLORS["badge_system"]
    return COLORS["badge_agent"]


def _bubble_colors(author: str) -> tuple[str, str]:
    key = author.lower().strip()
    if key == "operator":
        return COLORS["operator_bg"], COLORS["operator_text"]
    if key == "clems":
        return COLORS["clems_bg"], COLORS["clems_text"]
    if key == "system":
        return COLORS["system_bg"], COLORS["system_text"]
    return COLORS["agent_bg"], COLORS["agent_text"]


def _initials(author: str) -> str:
    key = author.lower().strip()
    if key == "operator":
        return "OP"
    if key == "clems":
        return "CL"
    if key == "system":
        return "SY"
    if key == "vulgarisation":
        return "VU"
    return key[:2].upper()


def _format_time(timestamp: str) -> str:
    if not timestamp:
        return ""
    if "T" in timestamp:
        time_part = timestamp.split("T", 1)[1]
        return time_part.split("+", 1)[0].replace("Z", "")[:5]
    return timestamp[:5]


# ── Avatar badge ──────────────────────────────────────────────────────
class AvatarWidget(QWidget):
    """Circular avatar badge with initials."""

    def __init__(self, initials: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._initials = initials
        self._color = QColor(color)
        self.setFixedSize(32, 32)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0.0, 0.0, 32.0, 32.0)
        painter.fillPath(path, self._color)
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Inter", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self._initials)
        painter.end()


# ── Chat bubble ───────────────────────────────────────────────────────
class ChatBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, payload: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chatBubble")
        author = payload.get("author", "system")
        text = payload.get("text", "")
        timestamp = payload.get("timestamp", "")
        is_operator = author.lower().strip() == "operator"
        bg_color, text_color = _bubble_colors(author)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(6)

        avatar = AvatarWidget(_initials(author), _badge_color(author))
        avatar.setToolTip(author.title())

        bubble = QFrame()
        bubble.setObjectName("bubbleFrame")
        bubble.setStyleSheet(
            f"#bubbleFrame {{ background: {bg_color}; border-radius: 12px; padding: 8px 12px; }}"
        )
        bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bubble.setMaximumWidth(300)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(2)

        name_label = QLabel(author.title())
        name_label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 11px;")

        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_label.setStyleSheet(f"color: {text_color}; font-size: 13px; line-height: 1.4;")

        time_label = QLabel(_format_time(timestamp))
        time_label.setStyleSheet(f"color: {COLORS['timestamp']}; font-size: 10px;")
        time_label.setAlignment(Qt.AlignRight)

        bubble_layout.addWidget(name_label)
        bubble_layout.addWidget(msg_label)
        bubble_layout.addWidget(time_label)

        if is_operator:
            outer.addStretch(1)
            outer.addWidget(bubble)
            outer.addWidget(avatar)
        else:
            outer.addWidget(avatar)
            outer.addWidget(bubble)
            outer.addStretch(1)

        self.setStyleSheet("background: transparent; border: none;")


# ── Typing indicator ─────────────────────────────────────────────────
class TypingIndicator(QFrame):
    """Animated typing indicator."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("typingIndicator")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(6)

        avatar = AvatarWidget("CL", COLORS["badge_clems"])

        bubble = QFrame()
        bubble.setStyleSheet(
            f"background: {COLORS['typing_bg']}; border-radius: 12px; padding: 8px 12px;"
        )

        layout = QHBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        self._dots_label = QLabel("Clems réfléchit")
        self._dots_label.setStyleSheet(
            f"color: {COLORS['typing_text']}; font-size: 12px; font-style: italic;"
        )
        layout.addWidget(self._dots_label)

        outer.addWidget(avatar)
        outer.addWidget(bubble)
        outer.addStretch(1)

        self.setStyleSheet("background: transparent; border: none;")

        self._dot_count = 0
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._animate)

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event: object) -> None:
        super().hideEvent(event)
        self._timer.stop()

    def _animate(self) -> None:
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        self._dots_label.setText(f"Clems réfléchit{dots}")


# ── Main chatroom widget ─────────────────────────────────────────────
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("chatHeader")
        header.setFixedHeight(44)
        header.setStyleSheet(
            f"#chatHeader {{ background: {COLORS['input_bg']}; border-bottom: 1px solid {COLORS['input_border']}; }}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        title = QLabel("💬 Chat — Clems AI")
        title.setStyleSheet("color: #E2E8F0; font-weight: bold; font-size: 14px;")
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #64748B; font-size: 11px;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self._status_label)

        # ── Scroll area for messages ──────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            f"#chatScrollArea {{ background: {COLORS['system_bg']}; border: none; }}"
            f"QScrollBar:vertical {{ background: {COLORS['input_bg']}; width: 6px; }}"
            f"QScrollBar::handle:vertical {{ background: {COLORS['input_border']}; border-radius: 3px; min-height: 20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
        )

        self.messages_container = QWidget()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_container.setStyleSheet(f"background: {COLORS['system_bg']};")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch(1)
        self.scroll_area.setWidget(self.messages_container)

        # ── Typing indicator ──────────────────────────────────────────
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.setVisible(False)

        # ── Composer ──────────────────────────────────────────────────
        composer = QFrame()
        composer.setObjectName("chatComposer")
        composer.setFixedHeight(52)
        composer.setStyleSheet(
            f"#chatComposer {{ background: {COLORS['input_bg']}; border-top: 1px solid {COLORS['input_border']}; }}"
        )
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(8, 8, 8, 8)
        composer_layout.setSpacing(6)

        self.input = QLineEdit()
        self.input.setObjectName("chatInput")
        self.input.setPlaceholderText("Écris un message à Clems...")
        self.input.setStyleSheet(
            f"#chatInput {{"
            f"  background: {COLORS['input_border']};"
            f"  color: {COLORS['input_text']};"
            f"  border: 1px solid #334155;"
            f"  border-radius: 18px;"
            f"  padding: 6px 14px;"
            f"  font-size: 13px;"
            f"}}"
            f"#chatInput:focus {{ border-color: {COLORS['send_bg']}; }}"
        )

        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("chatSendBtn")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(
            f"#chatSendBtn {{"
            f"  background: {COLORS['send_bg']};"
            f"  color: {COLORS['send_text']};"
            f"  border: none;"
            f"  border-radius: 18px;"
            f"  font-size: 16px;"
            f"  font-weight: bold;"
            f"}}"
            f"#chatSendBtn:hover {{ background: {COLORS['send_hover']}; }}"
        )

        composer_layout.addWidget(self.input, 1)
        composer_layout.addWidget(self.send_btn)

        # ── Assemble ──────────────────────────────────────────────────
        layout.addWidget(header)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.typing_indicator)
        layout.addWidget(composer)

        # ── Compatibility: keep old references alive for signals ──────
        # main_window connects:  chatroom.thread_selector.currentTextChanged
        # We create a dummy that never fires so no crash occurs.
        self.thread_selector = _DummyCombo()
        self.pack_light_btn = _DummyButton()
        self.pack_full_btn = _DummyButton()
        self.ping_btn = _DummyButton()
        self.voice_btn = _DummyButton()
        self.scene_btn = _DummyButton()

    # ── Typing indicator control ──────────────────────────────────────
    def show_typing(self) -> None:
        self.typing_indicator.setVisible(True)
        self._scroll_to_bottom()

    def hide_typing(self) -> None:
        self.typing_indicator.setVisible(False)

    # ── Status label ──────────────────────────────────────────────────
    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    # ── Message key for dedup ─────────────────────────────────────────
    def _message_key(self, payload: dict, index_hint: int) -> str:
        message_id = str(payload.get("message_id") or "").strip()
        if message_id:
            return message_id
        ts = str(payload.get("timestamp") or "")
        author = str(payload.get("author") or "")
        text = str(payload.get("text") or "")
        return f"{ts}|{author}|{text}|{index_hint}"

    # ── Render messages ───────────────────────────────────────────────
    def _clear_messages(self) -> None:
        """Remove all bubble widgets from the layout (keep the stretch)."""
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_bubble(self, payload: dict) -> None:
        """Add a bubble widget before the trailing stretch."""
        bubble = ChatBubble(payload)
        insert_index = max(0, self.messages_layout.count() - 1)
        self.messages_layout.insertWidget(insert_index, bubble)

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _should_rebuild(self, existing: list[str], incoming: list[str]) -> bool:
        if not existing:
            return True
        if len(incoming) < len(existing):
            return True
        for idx, key in enumerate(existing):
            if incoming[idx] != key:
                return True
        return False

    # ── Public API (same as old chatroom for compatibility) ────────────
    def set_global_messages(self, messages: list[dict]) -> None:
        bar = self.scroll_area.verticalScrollBar()
        at_bottom = (bar.maximum() - bar.value()) <= 4

        if not messages:
            self._clear_messages()
            self._global_keys = []
            return

        incoming_keys = [self._message_key(p, i) for i, p in enumerate(messages)]
        rebuilt = self._should_rebuild(self._global_keys, incoming_keys)

        if rebuilt:
            self._clear_messages()
            for payload in messages:
                self._add_bubble(payload)
        else:
            for payload in messages[len(self._global_keys):]:
                self._add_bubble(payload)

        self._global_keys = incoming_keys

        if at_bottom or rebuilt:
            self._scroll_to_bottom()

    def set_thread_tags(self, tags: list[str]) -> None:
        pass  # Threads not shown in simplified chat view

    def current_thread_tag(self) -> str:
        return ""

    def set_thread_messages(self, messages: list[dict], *, thread_tag: str = "") -> None:
        pass  # Threads not shown in simplified chat view

    def set_context_ref(self, context_ref: dict | None) -> None:
        if not isinstance(context_ref, dict):
            self._current_context_ref = None
            return
        self._current_context_ref = dict(context_ref)

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
        self._clear_messages()

    # ── Backward compat: format_message (used by some tests) ──────────
    def format_message(self, payload: dict) -> str:
        timestamp = _format_time(payload.get("timestamp", ""))
        author = payload.get("author", "operator")
        text = payload.get("text", "")
        if timestamp:
            return f"{timestamp} {author}: {text}"
        return f"{author}: {text}"


# ── Dummy widgets for backward compatibility ──────────────────────────
class _DummyCombo(QWidget):
    """No-op combo substitute so signal connections don't crash."""
    class _Signal:
        def connect(self, *_args: object) -> None:
            pass
    currentTextChanged = _Signal()
    def currentData(self) -> str:
        return ""

class _DummyButton(QWidget):
    """No-op button substitute."""
    class _Signal:
        def connect(self, *_args: object) -> None:
            pass
    clicked = _Signal()
