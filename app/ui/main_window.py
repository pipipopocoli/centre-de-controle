from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QSizePolicy, QVBoxLayout, QWidget

from app.data.model import ProjectData
from app.data.paths import PROJECTS_DIR, project_dir
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
        self.chatroom.input.returnPressed.connect(self.on_send_message)
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

        self._clems_seen: set[str] = set()
        self._clems_reminded_requests: set[str] = set()
        self._clems_pending_question_at: str | None = None
        self._clems_pinged_operator: bool = False
        self._clems_last_agent_ack_key: str | None = None

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(60000)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()

    def load_project(self, project: ProjectData) -> None:
        self.current_project_id = project.project_id
        self.roadmap.set_roadmap(
            project.roadmap.get("now", []),
            project.roadmap.get("next", []),
            project.roadmap.get("risks", []),
        )
        phase, objective, next_items = self._read_state_summary()
        self.roadmap.set_state(phase, objective, next_items)
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
        self._ack_agent_message(global_messages)
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
        message_id = self._make_message_id("operator")
        payload = {
            "message_id": message_id,
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
        self._auto_reply(payload)
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
        message_id = self._make_message_id("operator")
        payload = {
            "message_id": message_id,
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
        self._auto_reply(payload)
        self.refresh_chat()

    def _make_message_id(self, author: str) -> str:
        return f"msg_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{author}"

    def _message_key(self, payload: dict) -> str:
        return payload.get("message_id") or f"{payload.get('timestamp','')}|{payload.get('author','')}|{payload.get('text','')}"

    def _parse_sections(self, path: Path) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        if not path.exists():
            return sections
        current: str | None = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("## "):
                current = line[3:].strip()
                sections.setdefault(current, [])
                continue
            if current and line.startswith("-"):
                item = line.lstrip("-").strip()
                if item:
                    sections[current].append(item)
        return sections

    def _read_state_summary(self) -> tuple[str, str, list[str]]:
        if not self.current_project_id:
            return "", "", []
        state_path = project_dir(self.current_project_id) / "STATE.md"
        sections = self._parse_sections(state_path)
        phase = (sections.get("Phase") or [""])[0]
        objective = (sections.get("Objective") or [""])[0]
        next_items = sections.get("Next") or []
        return phase, objective, next_items

    def _build_clems_reply(self, text: str, mentions: list[str]) -> tuple[str, bool]:
        lower = text.lower()
        phase, objective, next_items = self._read_state_summary()

        if any(key in lower for key in ["next", "prochaine", "etape", "roadmap", "etat", "status"]):
            lines = ["Etat actuel:"]
            if phase:
                lines.append(f"- Phase: {phase}")
            if objective:
                lines.append(f"- Objectif: {objective}")
            if next_items:
                lines.append("- Next:")
                for item in next_items[:3]:
                    lines.append(f"  - {item}")
            return "\n".join(lines), False

        if any(key in lower for key in ["data", "dossier", "chemin", "projects"]):
            return f"Data dir actif: {PROJECTS_DIR}", False

        if any(key in lower for key in ["repond", "reponse", "personne", "reply"]):
            return "Les agents ne repondent pas automatiquement. Je ping les agents tags et je te reviens.", False

        ack = "Recu. Je m en occupe."
        if mentions:
            action = "Action: ping " + " ".join(f"@{m}" for m in mentions)
            return f"{ack}\n{action}", False
        question = "Peux tu preciser l objectif, le scope, et la deadline?"
        return f"{ack}\n{question}", True

    def _auto_reply(self, payload: dict) -> None:
        author = payload.get("author", "")
        if author != "operator":
            return
        if self._clems_pending_question_at:
            self._clems_pending_question_at = None
            self._clems_pinged_operator = False
        key = self._message_key(payload)
        if key in self._clems_seen:
            return
        self._clems_seen.add(key)

        text = str(payload.get("text", ""))
        mentions = payload.get("mentions") or []
        reply_text, asked = self._build_clems_reply(text, mentions)

        reply = {
            "message_id": self._make_message_id("clems"),
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "clems",
            "text": reply_text,
            "tags": [],
            "mentions": [],
            "event": "clems_autoreply",
            "reply_to": payload.get("message_id"),
        }
        append_chat_message(self.current_project_id, reply)
        self.refresh_chat()

        if asked:
            self._clems_pending_question_at = reply["timestamp"]
            self._clems_pinged_operator = False

    def _ack_agent_message(self, messages: list[dict]) -> None:
        if not messages:
            return
        last = messages[-1]
        author = last.get("author", "")
        if author in {"operator", "clems", "system"}:
            return
        if last.get("event", "").startswith("clems_"):
            return
        key = self._message_key(last)
        if self._clems_last_agent_ack_key == key:
            return
        ack = {
            "message_id": self._make_message_id("clems"),
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "clems",
            "text": f"Recu @{author}. Je te reviens si besoin.",
            "tags": [],
            "mentions": [],
            "event": "clems_ack",
        }
        append_chat_message(self.current_project_id, ack)
        self._clems_last_agent_ack_key = key

    def _parse_iso(self, value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def check_reminders(self) -> None:
        if not self.current_project_id:
            return
        now = datetime.now(timezone.utc)
        global_messages = load_chat_global(self.current_project_id)

        # Agent reminders (run requests)
        runs_path = project_dir(self.current_project_id) / "runs" / "requests.ndjson"
        if runs_path.exists():
            for raw in runs_path.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                try:
                    req = json.loads(raw)
                except Exception:
                    continue
                request_id = req.get("request_id")
                if not request_id or request_id in self._clems_reminded_requests:
                    continue
                if req.get("source") != "mention":
                    continue
                created_at = self._parse_iso(str(req.get("created_at", "")))
                agent_id = req.get("agent_id")
                if not created_at or not agent_id:
                    continue
                if now - created_at < timedelta(minutes=30):
                    continue
                replied = False
                for msg in reversed(global_messages[-200:]):
                    msg_time = self._parse_iso(str(msg.get("timestamp", "")))
                    if not msg_time or msg_time < created_at:
                        continue
                    if msg.get("author") == agent_id:
                        replied = True
                        break
                if replied:
                    self._clems_reminded_requests.add(request_id)
                    continue
                reminder = {
                    "message_id": self._make_message_id("clems"),
                    "timestamp": now.replace(microsecond=0).isoformat(),
                    "author": "clems",
                    "text": f"Rappel @{agent_id}: ping en attente.",
                    "tags": [],
                    "mentions": [agent_id],
                    "event": "clems_reminder",
                }
                append_chat_message(self.current_project_id, reminder)
                record_mentions(self.current_project_id, reminder)
                self._clems_reminded_requests.add(request_id)

        # Operator reminder after question
        if self._clems_pending_question_at and not self._clems_pinged_operator:
            asked_at = self._parse_iso(self._clems_pending_question_at)
            if asked_at and now - asked_at >= timedelta(hours=2):
                responded = False
                for msg in reversed(global_messages[-200:]):
                    msg_time = self._parse_iso(str(msg.get("timestamp", "")))
                    if not msg_time or msg_time <= asked_at:
                        continue
                    if msg.get("author") == "operator":
                        responded = True
                        break
                if not responded:
                    reminder = {
                        "message_id": self._make_message_id("clems"),
                        "timestamp": now.replace(microsecond=0).isoformat(),
                        "author": "clems",
                        "text": "Rappel: j attends ta reponse pour avancer.",
                        "tags": [],
                        "mentions": [],
                        "event": "clems_operator_reminder",
                    }
                    append_chat_message(self.current_project_id, reminder)
                    self._clems_pinged_operator = True
