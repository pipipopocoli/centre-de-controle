from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QSizePolicy, QVBoxLayout, QWidget

from app.data.model import ProjectData
from app.data.store import (
    append_chat_message,
    append_thread_message,
    list_chat_threads,
    load_chat_global,
    load_chat_thread,
    load_project,
    record_mentions,
)
from app.services.chat_parser import parse_mentions, parse_tags
from app.services.pack_context import build_pack_context, write_pack_context
from app.ui.agents_grid import AgentsGridWidget
from app.ui.chatroom import ChatroomWidget
from app.ui.roadmap import RoadmapWidget
from app.ui.sidebar import SidebarWidget


class MainWindow(QMainWindow):
    def __init__(
        self,
        project: ProjectData,
        projects: list[str] | None = None,
        version_text: str = "",
        data_dir: str = "",
    ) -> None:
        super().__init__()
        title = "Centre de controle"
        if version_text:
            title = f"{title} - {version_text}"
        self.setWindowTitle(title)
        self.resize(1400, 860)
        self.current_project_id = project.project_id

        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        footer_lines = []
        if version_text:
            footer_lines.append(version_text)
        if data_dir:
            footer_lines.append(f"Data: {data_dir}")
        footer_text = "\n".join(footer_lines) if footer_lines else None

        self.sidebar = SidebarWidget(projects=projects, footer_text=footer_text)
        self.sidebar.setFixedWidth(220)

        self.center = QWidget()
        center_layout = QVBoxLayout(self.center)
        center_layout.setContentsMargins(12, 12, 12, 12)
        center_layout.setSpacing(12)

        self.roadmap = RoadmapWidget()
        self.roadmap.setFixedHeight(180)

        self.agents_grid = AgentsGridWidget()
        self.agents_grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        center_layout.addWidget(self.roadmap)
        center_layout.addWidget(self.agents_grid, 1)

        self.chatroom = ChatroomWidget()
        self.chatroom.setFixedWidth(360)

        outer.addWidget(self.sidebar)
        outer.addWidget(self.center, 1)
        outer.addWidget(self.chatroom)

        self.setCentralWidget(central)

        self.sidebar.project_list.currentTextChanged.connect(self.on_project_selected)
        self.chatroom.send_btn.clicked.connect(self.on_send_message)
        self.chatroom.thread_selector.currentTextChanged.connect(self.on_thread_selected)
        self.chatroom.pack_light_btn.clicked.connect(self.on_pack_light)
        self.chatroom.pack_full_btn.clicked.connect(self.on_pack_full)
        self.chatroom.ping_btn.clicked.connect(self.on_ping_agents)
        if projects and project.project_id in projects:
            self.sidebar.project_list.setCurrentRow(projects.index(project.project_id))

        self.load_project(project)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.refresh_project)
        self.refresh_timer.start()

    def load_project(self, project: ProjectData) -> None:
        self.current_project_id = project.project_id
        self.roadmap.set_roadmap(
            project.roadmap.get("now", []),
            project.roadmap.get("next", []),
            project.roadmap.get("risks", []),
        )
        self.agents_grid.set_agents(project.agents)
        self.refresh_chat()

    def on_project_selected(self, project_id: str) -> None:
        if not project_id:
            return
        project = load_project(project_id)
        self.load_project(project)

    def refresh_project(self) -> None:
        if not self.current_project_id:
            return
        project = load_project(self.current_project_id)
        self.load_project(project)

    def refresh_chat(self) -> None:
        if not self.current_project_id:
            return
        global_messages = load_chat_global(self.current_project_id)
        self.chatroom.set_global_messages(global_messages)
        tags = list_chat_threads(self.current_project_id)
        self.chatroom.set_thread_tags(tags)
        current_tag = self.chatroom.current_thread_tag()
        if current_tag:
            messages = load_chat_thread(self.current_project_id, current_tag)
        else:
            messages = []
        self.chatroom.set_thread_messages(messages)

    def on_thread_selected(self, _label: str) -> None:
        self.refresh_chat()

    def on_send_message(self) -> None:
        if not self.current_project_id:
            return
        text = self.chatroom.input.text().strip()
        if not text:
            return
        tags = parse_tags(text)
        mentions = parse_mentions(text)
        payload = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "operator",
            "text": text,
            "tags": tags,
            "mentions": mentions,
        }
        append_chat_message(self.current_project_id, payload)
        for tag in tags:
            append_thread_message(self.current_project_id, tag, payload)
        record_mentions(self.current_project_id, payload)
        self.chatroom.input.clear()
        self.refresh_chat()

    def _emit_pack_feedback(self, mode: str, path: str) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "system",
            "text": f"Pack Context {mode} generated: {path}",
            "tags": ["pack"],
            "mentions": [],
        }
        append_chat_message(self.current_project_id, payload)
        append_thread_message(self.current_project_id, "pack", payload)
        self.refresh_chat()

    def on_pack_light(self) -> None:
        if not self.current_project_id:
            return
        content = build_pack_context(self.current_project_id, "light", None)
        path = write_pack_context(self.current_project_id, "light", content)
        QApplication.clipboard().setText(content)
        self._emit_pack_feedback("Light", str(path))

    def on_pack_full(self) -> None:
        if not self.current_project_id:
            return
        thread_tag = self.chatroom.current_thread_tag()
        content = build_pack_context(self.current_project_id, "full", thread_tag or None)
        path = write_pack_context(self.current_project_id, "full", content)
        QApplication.clipboard().setText(content)
        self._emit_pack_feedback("Full", str(path))

    def on_ping_agents(self) -> None:
        if not self.current_project_id:
            return
        text = "Ping @leo @victor #ping"
        tags = parse_tags(text)
        mentions = parse_mentions(text)
        payload = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "operator",
            "text": text,
            "tags": tags,
            "mentions": mentions,
        }
        append_chat_message(self.current_project_id, payload)
        for tag in tags:
            append_thread_message(self.current_project_id, tag, payload)
        record_mentions(self.current_project_id, payload)
        self.refresh_chat()
