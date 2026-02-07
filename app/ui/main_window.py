from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.data.paths import PROJECTS_DIR, project_dir
from app.data.store import (
    append_agent_journal,
    append_chat_message,
    append_thread_message,
    list_chat_threads,
    list_projects,
    load_chat_global,
    load_chat_thread,
    load_project,
    mark_agent_requests_done,
    record_mentions,
    save_project,
)
from app.services.brain_manager import BrainManager
from app.services.chat_parser import parse_mentions, parse_tags
from app.services.pack_context import build_pack_context, write_pack_context
from app.services.auto_mode import (
    dispatch_once as auto_mode_dispatch_once,
    iter_reminder_candidates,
    load_runtime_state,
    mark_agent_replied,
    mark_request_reminded,
)
from app.ui.agents_grid import AgentsGridWidget
from app.ui.chatroom import ChatroomWidget
from app.ui.roadmap import RoadmapWidget
from app.ui.sidebar import SidebarWidget

logger = logging.getLogger(__name__)


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
        # Data dir moved to Auto-Mode Panel
        footer_text = "\n".join(footer_lines) if footer_lines else None

        self.sidebar = SidebarWidget(projects=projects, footer_text=footer_text, data_dir=data_dir)
        self.sidebar.setFixedWidth(220)
        self.sidebar.new_project_btn.clicked.connect(self.on_new_project)

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
        self.sidebar.auto_mode.toggle.toggled.connect(self.on_auto_mode_toggled)
        self.sidebar.auto_mode.run_once_btn.clicked.connect(self.on_auto_mode_run_once)
        if projects and project.project_id in projects:
            self.sidebar.project_list.setCurrentRow(projects.index(project.project_id))

        self.brain_manager = BrainManager()

        # Auto-mode: default ON (can be overridden per project via settings.json).
        self.auto_mode_enabled = True
        self.auto_mode_interval_seconds = 5
        self.auto_mode_max_actions = 1
        self.auto_mode_codex_app = "Codex"
        self.auto_mode_ag_app = "Antigravity"
        self.auto_mode_last_error: str | None = None

        self.auto_mode_timer = QTimer(self)
        self.auto_mode_timer.setInterval(self.auto_mode_interval_seconds * 1000)
        self.auto_mode_timer.timeout.connect(self.run_auto_mode_tick)

        self.load_project(project)
        self.run_auto_mode_tick()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.refresh_project)
        self.refresh_timer.start()

        self._clems_seen: set[str] = set()
        self._clems_pending_question_at: str | None = None
        self._clems_pinged_operator: bool = False
        self._clems_last_agent_ack_key: str | None = None

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(60000)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()

    def load_project(self, project: ProjectData) -> None:
        prev_project_id = self.current_project_id
        self.current_project_id = project.project_id
        if prev_project_id != self.current_project_id:
            self.sidebar.auto_mode.set_last_dispatch("-")
            self.sidebar.auto_mode.set_last_error("")
            self.sidebar.auto_mode.set_pending(0)
        self.roadmap.set_roadmap(
            project.roadmap.get("now", []),
            project.roadmap.get("next", []),
            project.roadmap.get("risks", []),
        )
        phase, objective, next_items, eta = self._read_state_summary()
        self.roadmap.set_state(phase, objective, next_items, eta=eta)
        self.agents_grid.set_agents(project.agents)
        self._sync_auto_mode_from_settings(project)
        self.sidebar.auto_mode.set_pending(self._count_fresh_pending_requests())
        self.refresh_chat()

    def on_project_selected(self, project_id: str) -> None:
        if not project_id:
            return
        project = load_project(project_id)
        self.load_project(project)

    def _reload_projects_list(self, select_id: str | None = None) -> None:
        projects = list_projects()
        self.sidebar.project_list.blockSignals(True)
        self.sidebar.project_list.clear()
        if projects:
            self.sidebar.project_list.addItems(projects)
        if select_id and select_id in projects:
            self.sidebar.project_list.setCurrentRow(projects.index(select_id))
        self.sidebar.project_list.blockSignals(False)

    def on_new_project(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select project folder")
        if not folder:
            return
        repo_path = Path(folder)
        try:
            project_id = self.brain_manager.create_project_from_repo(repo_path)
            self.brain_manager.run_intake(project_id, repo_path)
        except Exception as exc:  # noqa: BLE001 - show error in chat log
            append_chat_message(
                self.current_project_id,
                {
                    "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    "author": "system",
                    "text": f"Intake failed: {exc}",
                    "tags": ["intake"],
                    "mentions": [],
                },
            )
            return
        self._reload_projects_list(select_id=project_id)
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
        # Auto-mode should react quickly to operator mentions (when enabled).
        self.run_auto_mode_tick()
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
        self.run_auto_mode_tick()
        self._auto_reply(payload)
        self.refresh_chat()

    def _settings_path(self, project_id: str) -> Path:
        return project_dir(project_id) / "settings.json"

    def _load_settings_json(self, project_id: str) -> dict:
        path = self._settings_path(project_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_settings_json(self, project_id: str, settings: dict) -> None:
        path = self._settings_path(project_id)
        settings["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def _sync_auto_mode_from_settings(self, project: ProjectData) -> None:
        # Read settings from loaded project (fast path).
        settings = project.settings if isinstance(project.settings, dict) else {}
        feature_flags = settings.get("feature_flags") if isinstance(settings.get("feature_flags"), dict) else {}
        enabled = feature_flags.get("auto_mode")
        if enabled is None:
            enabled = True

        auto_mode = settings.get("auto_mode") if isinstance(settings.get("auto_mode"), dict) else {}
        interval_seconds = auto_mode.get("interval_seconds", 5)
        max_actions = auto_mode.get("max_actions", 1)

        try:
            interval_seconds = int(interval_seconds)
        except (TypeError, ValueError):
            interval_seconds = 5
        try:
            max_actions = int(max_actions)
        except (TypeError, ValueError):
            max_actions = 1

        interval_seconds = max(1, min(interval_seconds, 60))
        max_actions = max(0, min(max_actions, 5))

        self.auto_mode_enabled = bool(enabled)
        self.auto_mode_interval_seconds = interval_seconds
        self.auto_mode_max_actions = max_actions

        self.sidebar.auto_mode.set_enabled(self.auto_mode_enabled)
        self.auto_mode_timer.setInterval(self.auto_mode_interval_seconds * 1000)
        if self.auto_mode_enabled and not self.auto_mode_timer.isActive():
            self.auto_mode_timer.start()
        if not self.auto_mode_enabled and self.auto_mode_timer.isActive():
            self.auto_mode_timer.stop()

    def _persist_auto_mode_settings(self) -> None:
        if not self.current_project_id:
            return
        settings = self._load_settings_json(self.current_project_id)
        feature_flags = settings.get("feature_flags")
        if not isinstance(feature_flags, dict):
            feature_flags = {}
            settings["feature_flags"] = feature_flags
        feature_flags["auto_mode"] = bool(self.auto_mode_enabled)

        auto_mode = settings.get("auto_mode")
        if not isinstance(auto_mode, dict):
            auto_mode = {}
            settings["auto_mode"] = auto_mode
        auto_mode["interval_seconds"] = int(self.auto_mode_interval_seconds)
        auto_mode["max_actions"] = int(self.auto_mode_max_actions)

        self._save_settings_json(self.current_project_id, settings)

    def on_auto_mode_toggled(self, enabled: bool) -> None:
        self.auto_mode_enabled = bool(enabled)
        self._persist_auto_mode_settings()
        if self.auto_mode_enabled:
            self.auto_mode_timer.start()
            self.run_auto_mode_tick(manual=True)
        else:
            self.auto_mode_timer.stop()
        self.sidebar.auto_mode.set_last_error("")

    def on_auto_mode_run_once(self) -> None:
        self.run_auto_mode_tick(manual=True)

    def run_auto_mode_tick(self, manual: bool = False) -> None:
        if not self.current_project_id:
            return
        if not self.auto_mode_enabled and not manual:
            return

        try:
            result = auto_mode_dispatch_once(
                PROJECTS_DIR,
                self.current_project_id,
                max_actions=self.auto_mode_max_actions,
                codex_app=self.auto_mode_codex_app,
                ag_app=self.auto_mode_ag_app,
            )
        except Exception as exc:
            self.auto_mode_last_error = str(exc)
            self.sidebar.auto_mode.set_last_error(f"Error: {self.auto_mode_last_error}")
            return

        self.sidebar.auto_mode.set_pending(self._count_fresh_pending_requests())

        # Apply at most max_actions actions (already capped).
        for action in result.actions:
            QApplication.clipboard().setText(action.prompt_text)
            completed = subprocess.run(
                ["open", "-a", action.app_to_open],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                self.auto_mode_last_error = (completed.stderr or completed.stdout or "open failed").strip()
                self.sidebar.auto_mode.set_last_error(f"Open error: {self.auto_mode_last_error}")
            else:
                self.sidebar.auto_mode.set_last_error("")
            now = datetime.now().strftime("%H:%M:%S")
            self.sidebar.auto_mode.set_last_dispatch(f"{now} @{action.agent_id} -> {action.app_to_open}")

        # If there was dispatch activity but no action (max_actions=0), still update status.
        if not result.actions and result.dispatched_count:
            now = datetime.now().strftime("%H:%M:%S")
            self.sidebar.auto_mode.set_last_dispatch(f"{now} dispatched {result.dispatched_count}")
        elif not result.actions and not result.dispatched_count and manual:
            now = datetime.now().strftime("%H:%M:%S")
            self.sidebar.auto_mode.set_last_dispatch(
                f"{now} no-op (skipped: reminder={result.skipped_reminder}, old={result.skipped_old}, duplicate={result.skipped_duplicate})"
            )

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

    def _read_state_summary(self) -> tuple[str, str, list[str], str | None]:
        if not self.current_project_id:
            return "", "", [], None
        state_path = project_dir(self.current_project_id) / "STATE.md"
        sections = self._parse_sections(state_path)
        phase = (sections.get("Phase") or [""])[0]
        objective = (sections.get("Objective") or [""])[0]
        next_items = sections.get("Next") or []
        eta = (sections.get("ETA") or sections.get("Estimate") or [""])[0]
        eta = eta.strip() or None
        return phase, objective, next_items, eta

    def _build_clems_reply(self, text: str, mentions: list[str]) -> tuple[str, bool]:
        lower = text.lower()
        phase, objective, next_items, eta = self._read_state_summary()

        if any(key in lower for key in ["next", "prochaine", "etape", "roadmap", "etat", "status"]):
            lines = ["Etat actuel:"]
            if phase:
                lines.append(f"- Etape: {phase}")
            if objective:
                lines.append(f"- Cible: {objective}")
            if eta:
                lines.append(f"- ETA: {eta}")
            if next_items:
                lines.append("- Suite:")
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

        response_ts = str(last.get("timestamp") or datetime.now(timezone.utc).replace(microsecond=0).isoformat())
        request_id: str | None = None
        try:
            mark_agent_requests_done(self.current_project_id, author, responded_at=response_ts)
            request_id = mark_agent_replied(
                PROJECTS_DIR,
                self.current_project_id,
                author,
                reply_message_id=str(last.get("message_id") or "") or None,
                replied_at=response_ts,
            )
            project = load_project(self.current_project_id)
            agent = next((a for a in project.agents if a.agent_id == author), None)
            if agent is not None:
                agent.status = "replied"
                agent.heartbeat = response_ts
                save_project(project)
            append_agent_journal(
                self.current_project_id,
                author,
                {
                    "timestamp": response_ts,
                    "event": "reply_ack",
                    "message_id": last.get("message_id"),
                    "request_id": request_id,
                    "from": author,
                },
            )
        except Exception:
            logger.exception("Failed to sync agent reply lifecycle for %s", author)
        self.sidebar.auto_mode.set_pending(self._count_fresh_pending_requests())

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
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _count_fresh_pending_requests(self) -> int:
        if not self.current_project_id:
            return 0
        now = datetime.now(timezone.utc)
        runtime = load_runtime_state(PROJECTS_DIR, self.current_project_id)
        requests = runtime.get("requests", {})
        if not isinstance(requests, dict):
            return 0
        pending = 0
        for req in requests.values():
            if not isinstance(req, dict):
                continue
            status = str(req.get("status") or "").strip().lower()
            if status not in {"queued", "dispatched", "reminded"}:
                continue
            created_at = self._parse_iso(str(req.get("dispatched_at") or req.get("created_at") or ""))
            if created_at and now - created_at > timedelta(hours=24):
                continue
            pending += 1
        return pending

    def check_reminders(self) -> None:
        if not self.current_project_id:
            return
        now = datetime.now(timezone.utc)
        global_messages = load_chat_global(self.current_project_id)
        try:
            candidates = iter_reminder_candidates(
                PROJECTS_DIR,
                self.current_project_id,
                min_age_minutes=30,
                cooldown_minutes=60,
                max_reminders=3,
            )
            for candidate in candidates:
                request_id = str(candidate.get("request_id") or "").strip()
                agent_id = str(candidate.get("agent_id") or "").strip()
                if not request_id or not agent_id or agent_id == "clems":
                    continue

                created_at = self._parse_iso(str(candidate.get("dispatched_at") or candidate.get("created_at") or ""))
                replied_message: dict | None = None
                for msg in reversed(global_messages[-500:]):
                    msg_time = self._parse_iso(str(msg.get("timestamp", "")))
                    if not msg_time:
                        continue
                    if created_at and msg_time < created_at:
                        continue
                    if msg.get("author") == agent_id:
                        replied_message = msg
                        break

                if replied_message is not None:
                    reply_ts = str(replied_message.get("timestamp") or now.replace(microsecond=0).isoformat())
                    mark_agent_requests_done(self.current_project_id, agent_id, responded_at=reply_ts)
                    mark_agent_replied(
                        PROJECTS_DIR,
                        self.current_project_id,
                        agent_id,
                        reply_message_id=str(replied_message.get("message_id") or "") or None,
                        replied_at=reply_ts,
                    )
                    append_agent_journal(
                        self.current_project_id,
                        agent_id,
                        {
                            "timestamp": reply_ts,
                            "event": "reply_ack",
                            "message_id": replied_message.get("message_id"),
                            "request_id": request_id,
                            "from": agent_id,
                        },
                    )
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
                reminder_status = mark_request_reminded(
                    PROJECTS_DIR,
                    self.current_project_id,
                    request_id,
                    reminded_at=reminder["timestamp"],
                    max_reminders=3,
                )
                if reminder_status.get("status") == "closed":
                    close_note = {
                        "message_id": self._make_message_id("system"),
                        "timestamp": now.replace(microsecond=0).isoformat(),
                        "author": "system",
                        "text": f"Request {request_id} closed after 3 reminders for @{agent_id}.",
                        "tags": ["runs"],
                        "mentions": [],
                        "event": "request_closed",
                    }
                    append_chat_message(self.current_project_id, close_note)
                    append_agent_journal(
                        self.current_project_id,
                        agent_id,
                        {
                            "timestamp": close_note["timestamp"],
                            "event": "request_closed",
                            "request_id": request_id,
                            "reason": "max_reminders_reached",
                        },
                    )
        except Exception:
            logger.exception("Reminder lifecycle check failed for project=%s", self.current_project_id)

        self.sidebar.auto_mode.set_pending(self._count_fresh_pending_requests())

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
