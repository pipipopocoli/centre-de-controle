from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.data.paths import PROJECTS_DIR, project_dir
from app.data.store import (
    archive_ping_reminders,
    append_chat_message,
    append_thread_message,
    list_chat_threads,
    list_projects,
    load_chat_global,
    load_chat_thread,
    load_project,
    record_mentions,
)
from app.services.brain_manager import BrainManager
from app.services.chat_parser import parse_mentions, parse_tags
from app.services.llm_chat import send_message_async as llm_send_async, reset_history as llm_reset_history
from app.services.pack_context import build_pack_context, write_pack_context
from app.services.auto_mode import dispatch_once as auto_mode_dispatch_once
from app.services.auto_send import SendRoute, send_action
from app.services.takeover_wizard import TakeoverWizardResult, run_takeover_wizard
from app.services.wizard_live import (
    WizardLiveResult,
    load_wizard_live_session,
    parse_wizard_live_command,
    run_wizard_live_turn,
    start_wizard_live_session,
    stop_wizard_live_session,
)
from app.services.cloud_api_client import (
    get_llm_profile as api_get_llm_profile,
    get_pixel_feed as api_get_pixel_feed,
    post_agentic_turn as api_post_agentic_turn,
    post_chat_message as api_post_chat_message,
    post_voice_transcribe as api_post_voice_transcribe,
    put_llm_profile as api_put_llm_profile,
)
from app.services.pixel_feed_local import build_local_pixel_feed
from app.ui.agents_grid import AgentsGridWidget
from app.ui.chatroom import ChatroomWidget
from app.ui.doc_viewer import DocsViewerWidget
from app.ui.model_routing import ModelRoutingWidget
from app.ui.project_bible import ProjectBibleWidget
from app.ui.project_pilotage import ProjectPilotageWidget
from app.ui.pixel_view import PixelViewWidget
from app.ui.roadmap import RoadmapWidget
from app.ui.sidebar import SidebarWidget


class TakeoverWizardSignals(QObject):
    started = Signal(str)
    finished = Signal(object)
    failed = Signal(str)


class WizardLiveSignals(QObject):
    started = Signal(str)
    finished = Signal(object)
    failed = Signal(str)


class LLMChatSignals(QObject):
    response_ready = Signal(str, str)  # (response_text, reply_to_message_id)
    error = Signal(str)


class MainWindow(QMainWindow):
    def __init__(
        self,
        project: ProjectData,
        projects: list[str] | None = None,
        version_text: str = "",
        app_stamp: str = "",
        repo_head: str = "",
        data_dir: str = "",
        runtime_mode: str = "",
        runtime_source: str = "",
    ) -> None:
        super().__init__()
        title = "Cockpit"
        if version_text:
            title = f"{title} - {version_text}"
        self.setWindowTitle(title)
        self.resize(1400, 860)
        self.current_project_id = project.project_id
        self.api_strict_mode = str(os.environ.get("COCKPIT_API_STRICT_WRITES") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.app_stamp = app_stamp or version_text
        self.repo_head = repo_head
        self.runtime_mode = runtime_mode or "DEV LIVE"
        self.runtime_source = runtime_source or "custom"
        self.runtime_root = data_dir or ""

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
        self.sidebar.set_runtime_context(
            self.app_stamp,
            self.repo_head,
            self.current_project_id,
            runtime_mode=self.runtime_mode,
            runtime_source=self.runtime_source,
            runtime_root=self.runtime_root,
        )
        self.sidebar.setFixedWidth(220)
        self.sidebar.new_project_btn.clicked.connect(self.on_new_project)
        self.sidebar.takeover_wizard_btn.clicked.connect(self.on_takeover_wizard_clicked)

        # ── Center: tabbed panels ──────────────────────────────────
        self.center = QWidget()
        center_layout = QVBoxLayout(self.center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.center_tabs = QTabWidget()
        self.center_tabs.setObjectName("centerTabs")

        # Tab 1: Overview (Roadmap + Agents)
        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(12, 12, 12, 12)
        overview_layout.setSpacing(12)

        self.roadmap = RoadmapWidget()
        self.roadmap.setFixedHeight(180)

        self.agents_grid = AgentsGridWidget()
        self.agents_grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        overview_layout.addWidget(self.roadmap)
        overview_layout.addWidget(self.agents_grid, 1)

        self.center_tabs.addTab(overview, "Overview")

        # Tab 2: Vulgarisation
        self.project_bible = ProjectBibleWidget()
        self.center_tabs.addTab(self.project_bible, "Vulgarisation")

        # Tab 3: Pilotage (with visual timeline)
        self.project_pilotage = ProjectPilotageWidget()
        self.center_tabs.addTab(self.project_pilotage, "Pilotage")

        # Tab 4: Docs (Roadmap + Tournament HTML)
        self.docs_viewer = DocsViewerWidget()
        self.center_tabs.addTab(self.docs_viewer, "Docs")

        # Tab 5: Model routing (OpenRouter)
        self.model_routing = ModelRoutingWidget()
        self.center_tabs.addTab(self.model_routing, "Model Routing")

        # Tab 6: Pixel activity heatmap
        self.pixel_view = PixelViewWidget()
        self.center_tabs.addTab(self.pixel_view, "Pixel View")

        # Corner Widget for UI Toggles
        self.corner_widget = QWidget()
        corner_layout = QHBoxLayout(self.corner_widget)
        corner_layout.setContentsMargins(0, 0, 8, 0)
        corner_layout.setSpacing(8)

        self.toggle_sidebar_btn = QPushButton("≡ Sidebar")
        self.toggle_sidebar_btn.setCheckable(True)
        self.toggle_sidebar_btn.setChecked(True)
        self.toggle_sidebar_btn.setFlat(True)
        self.toggle_sidebar_btn.setStyleSheet("color: #5E6167; font-weight: bold; border: none;")
        self.toggle_sidebar_btn.toggled.connect(self._toggle_sidebar_visibility)

        self.toggle_chat_btn = QPushButton("Chat 💬")
        self.toggle_chat_btn.setCheckable(True)
        self.toggle_chat_btn.setChecked(True)
        self.toggle_chat_btn.setFlat(True)
        self.toggle_chat_btn.setStyleSheet("color: #5E6167; font-weight: bold; border: none;")
        self.toggle_chat_btn.toggled.connect(self._toggle_chat_visibility)

        corner_layout.addWidget(self.toggle_sidebar_btn)
        corner_layout.addWidget(self.toggle_chat_btn)
        self.center_tabs.setCornerWidget(self.corner_widget, Qt.TopRightCorner)

        center_layout.addWidget(self.center_tabs)

        self.chatroom = ChatroomWidget()
        self.chatroom.setFixedWidth(360)

        outer.addWidget(self.sidebar)
        outer.addWidget(self.center, 1)
        outer.addWidget(self.chatroom)

        self.setCentralWidget(central)

        initial_project_row: int | None = None
        if projects and project.project_id in projects:
            initial_project_row = projects.index(project.project_id)

        self.sidebar.project_list.currentTextChanged.connect(self.on_project_selected)
        self.chatroom.send_btn.clicked.connect(self.on_send_message)
        self.chatroom.input.returnPressed.connect(self.on_send_message)
        self.chatroom.thread_selector.currentTextChanged.connect(self.on_thread_selected)
        self.chatroom.pack_light_btn.clicked.connect(self.on_pack_light)
        self.chatroom.pack_full_btn.clicked.connect(self.on_pack_full)
        self.chatroom.ping_btn.clicked.connect(self.on_ping_agents)
        self.chatroom.voice_btn.clicked.connect(self.on_voice_transcribe_clicked)
        self.chatroom.scene_btn.clicked.connect(self.on_scene_turn_clicked)
        self.model_routing.load_requested.connect(self.on_load_model_routing)
        self.model_routing.save_requested.connect(self.on_save_model_routing)
        self.pixel_view.window_selector.currentIndexChanged.connect(self.refresh_pixel_feed)
        self.sidebar.docs_btn.clicked.connect(self.on_show_docs)
        self.agents_grid.context_selected.connect(self.on_ui_context_selected)
        self.project_pilotage.context_selected.connect(self.on_ui_context_selected)
        self.sidebar.auto_mode.toggle.toggled.connect(self.on_auto_mode_toggled)
        self.sidebar.auto_mode.run_once_btn.clicked.connect(self.on_auto_mode_run_once)
        self.sidebar.auto_mode.auto_send_toggle.toggled.connect(self.on_auto_send_toggled)

        self._takeover_wizard_running = False
        self._takeover_signals = TakeoverWizardSignals()
        self._takeover_signals.started.connect(self._on_takeover_wizard_started)
        self._takeover_signals.finished.connect(self._on_takeover_wizard_finished)
        self._takeover_signals.failed.connect(self._on_takeover_wizard_failed)
        self._wizard_live_running = False
        self._wizard_live_session_active = False
        self._wizard_live_pending_action: dict | None = None
        self._wizard_live_repo_path: Path | None = None
        self._wizard_live_signals = WizardLiveSignals()
        self._wizard_live_signals.started.connect(self._on_wizard_live_started)
        self._wizard_live_signals.finished.connect(self._on_wizard_live_finished)
        self._wizard_live_signals.failed.connect(self._on_wizard_live_failed)
        self.agent_ping_reminders_enabled = str(os.environ.get("COCKPIT_ENABLE_AGENT_PING_REMINDERS") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self._ping_archive_done_projects: set[str] = set()

        self._llm_chat_signals = LLMChatSignals()
        self._llm_chat_signals.response_ready.connect(self._on_llm_chat_response)
        self._llm_chat_signals.error.connect(self._on_llm_chat_error)

        self.brain_manager = BrainManager()

        # Runtime chat/reminder state must exist before first load_project().
        self._clems_seen: set[str] = set()
        self._clems_reminded_requests: set[str] = set()
        self._clems_pending_question_at: str | None = None
        self._clems_pinged_operator: bool = False
        self._clems_last_agent_ack_key: str | None = None

        # Auto-mode: default ON (can be overridden per project via settings.json).
        self.auto_mode_enabled = True
        self.auto_mode_interval_seconds = 5
        self.auto_mode_max_actions = 1
        self.auto_send_enabled = False
        self.auto_mode_codex_app = "OpenRouter"
        self.auto_mode_ag_app = "OpenRouter"
        self.auto_mode_last_error: str | None = None
        self._portfolio_cache: list[ProjectData] = []
        self._portfolio_cache_at: datetime | None = None
        self._portfolio_cache_seconds = 30
        self._last_bible_refresh_at: datetime | None = None
        self._bible_refresh_seconds = 45

        self.auto_mode_timer = QTimer(self)
        self.auto_mode_timer.setInterval(self.auto_mode_interval_seconds * 1000)
        self.auto_mode_timer.timeout.connect(self.run_auto_mode_tick)

        self._clems_seen: set[str] = set()
        self._clems_reminded_requests: set[str] = set()
        self._clems_pending_question_at: str | None = None
        self._clems_pinged_operator: bool = False
        self._clems_last_agent_ack_key: str | None = None

        self.load_project(project, refresh_chat_now=True, force_portfolio_refresh=True)
        if initial_project_row is not None:
            self.sidebar.project_list.blockSignals(True)
            self.sidebar.project_list.setCurrentRow(initial_project_row)
            self.sidebar.project_list.blockSignals(False)
        if self.api_strict_mode:
            self.sidebar.status_banner.show_warning("API strict mode: local runtime writes are disabled.")
        else:
            self.run_auto_mode_tick()

        self.project_refresh_timer = QTimer(self)
        self.project_refresh_timer.setInterval(5000)
        self.project_refresh_timer.timeout.connect(self.refresh_project)
        self.project_refresh_timer.start()

        self.pixel_refresh_timer = QTimer(self)
        self.pixel_refresh_timer.setInterval(7000)
        self.pixel_refresh_timer.timeout.connect(self.refresh_pixel_feed)
        self.pixel_refresh_timer.start()

        self.chat_refresh_timer = QTimer(self)
        self.chat_refresh_timer.setInterval(1500)
        self.chat_refresh_timer.timeout.connect(self.refresh_chat)
        self.chat_refresh_timer.start()

        self.bible_refresh_timer = QTimer(self)
        self.bible_refresh_timer.setInterval(15000)
        self.bible_refresh_timer.timeout.connect(self.refresh_bible)
        self.bible_refresh_timer.start()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(60000)
        self.reminder_timer.timeout.connect(self.check_reminders)
        if not self.api_strict_mode:
            self.reminder_timer.start()

    def _block_if_api_strict(self, action: str) -> bool:
        if not self.api_strict_mode:
            return False
        self.sidebar.status_banner.show_error(
            f"API strict mode: local action blocked ({action}). Use Cockpit API endpoints."
        )
        return True

    def load_project(
        self,
        project: ProjectData,
        *,
        refresh_chat_now: bool = True,
        force_portfolio_refresh: bool = False,
    ) -> None:
        prev_project_id = self.current_project_id
        self.current_project_id = project.project_id
        project_changed = prev_project_id != self.current_project_id
        self._sync_wizard_live_session_from_disk()
        self.sidebar.set_runtime_context(
            self.app_stamp,
            self.repo_head,
            self.current_project_id,
            runtime_mode=self.runtime_mode,
            runtime_source=self.runtime_source,
            runtime_root=self.runtime_root,
        )
        if project_changed:
            self.sidebar.auto_mode.set_last_dispatch("-")
            self.sidebar.auto_mode.set_last_error("")
            self.chatroom.reset_feed_state()
            self.chatroom.clear_context_ref()
            self._wizard_live_pending_action = None
        self._archive_ping_messages_once()
        self.roadmap.set_roadmap(
            project.roadmap.get("now", []),
            project.roadmap.get("next", []),
            project.roadmap.get("risks", []),
        )
        phase, objective, next_items, eta = self._read_state_summary()
        self.roadmap.set_state(phase, objective, next_items, eta=eta)
        self.agents_grid.set_agents(project.agents)
        self.project_bible.set_project(project, refresh=project_changed)
        portfolio_projects = self._get_portfolio_projects(project, force=force_portfolio_refresh or project_changed)
        self.project_pilotage.set_project(project, portfolio=portfolio_projects, refresh=True)
        self._sync_auto_mode_from_settings(project)
        self.refresh_model_routing_from_settings()
        self.refresh_pixel_feed()
        if refresh_chat_now:
            self.refresh_chat()
        if project_changed:
            self.refresh_bible(force=True)

    def _get_portfolio_projects(self, current_project: ProjectData, *, force: bool = False) -> list[ProjectData]:
        now = datetime.now(timezone.utc)
        if (
            not force
            and self._portfolio_cache_at is not None
            and (now - self._portfolio_cache_at).total_seconds() <= self._portfolio_cache_seconds
        ):
            cached = [item for item in self._portfolio_cache if item.project_id != current_project.project_id]
            return [current_project] + cached

        refreshed: list[ProjectData] = [current_project]
        for project_id in list_projects():
            if project_id == current_project.project_id:
                continue
            try:
                refreshed.append(load_project(project_id))
            except Exception:
                continue

        self._portfolio_cache = [item for item in refreshed if item.project_id != current_project.project_id]
        self._portfolio_cache_at = now
        return refreshed

    def on_project_selected(self, project_id: str) -> None:
        if not project_id:
            return
        project = load_project(project_id)
        self.load_project(project, refresh_chat_now=True, force_portfolio_refresh=True)

    def _reload_projects_list(self, select_id: str | None = None) -> None:
        projects = list_projects()
        self.sidebar.project_list.blockSignals(True)
        self.sidebar.project_list.clear()
        if projects:
            self.sidebar.project_list.addItems(projects)
        if select_id and select_id in projects:
            self.sidebar.project_list.setCurrentRow(projects.index(select_id))
        self.sidebar.project_list.blockSignals(False)

    def on_show_docs(self) -> None:
        self.center_tabs.setCurrentWidget(self.docs_viewer)

    def on_new_project(self) -> None:
        if self._block_if_api_strict("new_project"):
            return
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
        self.load_project(project, refresh_chat_now=True, force_portfolio_refresh=True)
        self._autokick_wizard_live(source="new_project", repo_path=repo_path)

    def refresh_project(self) -> None:
        if not self.current_project_id:
            return
        project = load_project(self.current_project_id)
        self.load_project(project, refresh_chat_now=False, force_portfolio_refresh=False)
        self.refresh_bible(force=False)
        self.refresh_pixel_feed()

    def refresh_bible(self, *, force: bool = False) -> None:
        if not self.current_project_id:
            return
        if self.center_tabs.currentWidget() is not self.project_bible and not force:
            return
        now = datetime.now(timezone.utc)
        if not force and self._last_bible_refresh_at is not None:
            elapsed = (now - self._last_bible_refresh_at).total_seconds()
            if elapsed < self._bible_refresh_seconds:
                return
        self.project_bible.refresh_content()
        self._last_bible_refresh_at = now

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
        self.chatroom.set_thread_messages(messages, thread_tag=current_tag)

    def on_thread_selected(self, _label: str) -> None:
        self.refresh_chat()

    def on_ui_context_selected(self, context_ref: dict) -> None:
        if not isinstance(context_ref, dict):
            return
        payload = dict(context_ref)
        if not payload.get("selected_at"):
            payload["selected_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        source_path = str(payload.get("source_path") or "").strip()
        if payload.get("kind") == "agent" and not source_path and self.current_project_id:
            agent_id = str(payload.get("id") or "").strip()
            if agent_id:
                state_path = project_dir(self.current_project_id) / "agents" / agent_id / "state.json"
                if state_path.exists():
                    payload["source_path"] = str(state_path)
                    try:
                        payload["source_uri"] = state_path.resolve().as_uri()
                    except Exception:
                        payload["source_uri"] = ""
        self.chatroom.set_context_ref(payload)

    def on_send_message(self) -> None:
        if not self.current_project_id:
            return
        text = self.chatroom.input.text().strip()
        if not text:
            return
        if self.api_strict_mode:
            self._send_message_via_api(text)
            return
        context_ref = self.chatroom.consume_context_ref()
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
        if context_ref:
            payload["context_ref"] = context_ref
        append_chat_message(self.current_project_id, payload)
        for tag in tags:
            append_thread_message(self.current_project_id, tag, payload)
        record_mentions(self.current_project_id, payload)
        wizard_live_command, wizard_live_body = parse_wizard_live_command(text)
        suppress_auto_reply = False
        if wizard_live_command:
            self._handle_wizard_live_command(wizard_live_command, wizard_live_body)
            suppress_auto_reply = True
        elif self._wizard_live_session_active:
            repo_path = self._resolve_wizard_live_repo_path(allow_picker=False)
            if repo_path is not None:
                self._queue_wizard_live_action(
                    mode="run",
                    trigger="wizard_live_session_message",
                    operator_message=text,
                    include_full_intake=False,
                    repo_path=repo_path,
                )
        # Auto-mode should react quickly to operator mentions (when enabled).
        self.run_auto_mode_tick()
        self._maybe_trigger_takeover_wizard(text, tags)
        if not suppress_auto_reply:
            self._auto_reply(payload)
        self.chatroom.input.clear()
        self.refresh_chat()

    def _send_message_via_api(self, text: str) -> None:
        thread_tag = self.chatroom.current_thread_tag() or None
        wizard_live_command, wizard_live_body = parse_wizard_live_command(text)
        if wizard_live_command:
            self._handle_wizard_live_command(wizard_live_command, wizard_live_body)
            self.chatroom.input.clear()
            return
        try:
            api_post_chat_message(self.current_project_id, text, thread_id=thread_tag)
            response = api_post_agentic_turn(self.current_project_id, text, mode="chat", thread_id=thread_tag)
        except Exception as exc:  # noqa: BLE001
            self.sidebar.status_banner.show_error(f"API chat send failed: {exc}")
            return
        run_id = str(response.get("run_id") or "-")
        status = str(response.get("status") or "unknown")
        self.sidebar.status_banner.show_warning(f"Agentic chat turn: {run_id} ({status})")
        self.chatroom.input.clear()
        self.refresh_chat()
        self.refresh_project()

    def on_scene_turn_clicked(self) -> None:
        if not self.current_project_id:
            return
        text = self.chatroom.input.text().strip()
        if not text:
            self.sidebar.status_banner.show_warning("Scène: ajoute d abord un message.")
            return
        if self.api_strict_mode:
            try:
                response = api_post_agentic_turn(
                    self.current_project_id,
                    text,
                    mode="scene",
                    thread_id=self.chatroom.current_thread_tag() or None,
                )
            except Exception as exc:  # noqa: BLE001
                self.sidebar.status_banner.show_error(f"Scene turn failed: {exc}")
                return
            run_id = str(response.get("run_id") or "-")
            spawned = int(response.get("spawned_agents_count") or 0)
            self.sidebar.status_banner.show_warning(f"Scène complete: {run_id} (spawn={spawned})")
            self.chatroom.input.clear()
            self.refresh_chat()
            self.refresh_project()
            return

        payload = {
            "message_id": self._make_message_id("operator"),
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "operator",
            "text": f"[scene] {text}",
            "tags": ["scene"],
            "mentions": [],
        }
        append_chat_message(self.current_project_id, payload)
        self._auto_reply(payload)
        self.chatroom.input.clear()
        self.refresh_chat()

    def on_voice_transcribe_clicked(self) -> None:
        if not self.current_project_id:
            return
        if not self.api_strict_mode:
            self.sidebar.status_banner.show_error("Vocal transcription requires API strict mode.")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select audio file",
            "",
            "Audio files (*.wav *.m4a *.mp3 *.ogg)",
        )
        if not file_path:
            return
        candidate = Path(file_path)
        if not candidate.exists():
            self.sidebar.status_banner.show_error("Audio file not found.")
            return
        raw = candidate.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        ext = candidate.suffix.lower().lstrip(".")
        audio_format = ext if ext in {"wav", "m4a", "mp3", "ogg"} else "wav"
        try:
            payload = api_post_voice_transcribe(
                self.current_project_id,
                audio_base64=encoded,
                audio_format=audio_format,
            )
        except Exception as exc:  # noqa: BLE001
            self.sidebar.status_banner.show_error(f"Voice transcription failed: {exc}")
            return
        transcript = str(payload.get("text") or "").strip()
        if transcript:
            self.chatroom.input.setText(transcript)
            self.sidebar.status_banner.show_warning("Voice transcribed into composer.")
        else:
            self.sidebar.status_banner.show_warning("Voice transcription returned empty text.")

    def _linked_repo_path(self) -> Path | None:
        if not self.current_project_id:
            return None
        settings = self._load_settings_json(self.current_project_id)
        raw = str(settings.get("linked_repo_path") or "").strip()
        if not raw:
            return None
        candidate = Path(raw).expanduser()
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate.absolute()
        return resolved if resolved.exists() else None

    def _sync_wizard_live_session_from_disk(self) -> None:
        if not self.current_project_id:
            self._wizard_live_session_active = False
            self._wizard_live_repo_path = None
            return
        payload = load_wizard_live_session(PROJECTS_DIR, self.current_project_id)
        self._wizard_live_session_active = bool(payload.get("active"))
        repo_raw = str(payload.get("repo_path") or "").strip()
        if not repo_raw:
            self._wizard_live_repo_path = self._linked_repo_path()
            return
        candidate = Path(repo_raw).expanduser()
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate.absolute()
        self._wizard_live_repo_path = resolved if resolved.exists() else self._linked_repo_path()

    def _pick_wizard_live_repo_path(self) -> Path | None:
        folder = QFileDialog.getExistingDirectory(self, "Select repo folder for Wizard Live")
        if not folder:
            return None
        repo_path = Path(folder).expanduser()
        settings = self._load_settings_json(self.current_project_id)
        settings["linked_repo_path"] = str(repo_path)
        self._save_settings_json(self.current_project_id, settings)
        return repo_path

    def _resolve_wizard_live_repo_path(self, *, allow_picker: bool) -> Path | None:
        if self._wizard_live_repo_path is not None and self._wizard_live_repo_path.exists():
            return self._wizard_live_repo_path
        linked = self._linked_repo_path()
        if linked is not None:
            self._wizard_live_repo_path = linked
            return linked
        if not allow_picker:
            return None
        picked = self._pick_wizard_live_repo_path()
        if picked is None:
            return None
        try:
            resolved = picked.resolve()
        except OSError:
            resolved = picked.absolute()
        self._wizard_live_repo_path = resolved
        return resolved

    def _queue_wizard_live_action(
        self,
        *,
        mode: str,
        trigger: str,
        operator_message: str,
        include_full_intake: bool,
        repo_path: Path | None,
    ) -> None:
        action = {
            "mode": mode,
            "trigger": trigger,
            "operator_message": operator_message,
            "include_full_intake": bool(include_full_intake),
            "repo_path": repo_path,
        }
        if self._wizard_live_running:
            self._wizard_live_pending_action = action
            self.sidebar.status_banner.show_warning("Wizard Live busy: last action queued.")
            return
        self._run_wizard_live_action(**action)

    def _run_wizard_live_action(
        self,
        *,
        mode: str,
        trigger: str,
        operator_message: str,
        include_full_intake: bool,
        repo_path: Path | None,
    ) -> None:
        if not self.current_project_id:
            return
        if mode in {"start", "run"} and repo_path is None:
            self.sidebar.status_banner.show_error("Wizard Live requires a linked repo path.")
            return
        project_id = self.current_project_id
        self._wizard_live_running = True
        target = str(repo_path) if repo_path is not None else "-"
        self._wizard_live_signals.started.emit(f"Wizard Live {mode} started ({target}) ...")

        def _worker() -> None:
            try:
                if mode == "start":
                    result = start_wizard_live_session(
                        projects_root=PROJECTS_DIR,
                        project_id=project_id,
                        repo_path=repo_path or Path("."),
                        operator_message=operator_message,
                        trigger=trigger,
                        run_initial=True,
                    )
                elif mode == "stop":
                    result = stop_wizard_live_session(
                        projects_root=PROJECTS_DIR,
                        project_id=project_id,
                        trigger=trigger,
                        reason=operator_message,
                    )
                else:
                    result = run_wizard_live_turn(
                        projects_root=PROJECTS_DIR,
                        project_id=project_id,
                        repo_path=repo_path or Path("."),
                        trigger=trigger,
                        operator_message=operator_message,
                        include_full_intake=include_full_intake,
                        session_active=self._wizard_live_session_active,
                    )
            except Exception as exc:  # noqa: BLE001
                self._wizard_live_signals.failed.emit(str(exc))
                return
            self._wizard_live_signals.finished.emit(result)

        threading.Thread(target=_worker, daemon=True).start()

    def _drain_pending_wizard_live_action(self) -> None:
        if self._wizard_live_running:
            return
        if not isinstance(self._wizard_live_pending_action, dict):
            return
        action = dict(self._wizard_live_pending_action)
        self._wizard_live_pending_action = None
        self._run_wizard_live_action(
            mode=str(action.get("mode") or "run"),
            trigger=str(action.get("trigger") or "wizard_live_queued"),
            operator_message=str(action.get("operator_message") or ""),
            include_full_intake=bool(action.get("include_full_intake")),
            repo_path=action.get("repo_path") if isinstance(action.get("repo_path"), Path) else None,
        )

    def _on_wizard_live_started(self, msg: str) -> None:
        self.sidebar.status_banner.show_warning(msg)

    def _on_wizard_live_finished(self, result: object) -> None:
        self._wizard_live_running = False
        if isinstance(result, WizardLiveResult):
            if result.repo_path:
                repo_candidate = Path(result.repo_path).expanduser()
                try:
                    self._wizard_live_repo_path = repo_candidate.resolve()
                except OSError:
                    self._wizard_live_repo_path = repo_candidate.absolute()
            self._wizard_live_session_active = bool(result.session_active)
            if result.status == "stopped":
                self.sidebar.status_banner.show_warning("Wizard Live stopped.")
            elif result.status == "ok":
                self.sidebar.status_banner.show_warning(f"Wizard Live complete: {result.run_id}")
            elif result.status == "degraded":
                self.sidebar.status_banner.show_warning("Wizard Live session started in degraded mode.")
            elif result.status == "failed":
                self.sidebar.status_banner.show_error(f"Wizard Live failed: {result.error or 'unknown error'}")
            elif result.status == "started":
                self.sidebar.status_banner.show_warning("Wizard Live session started.")
        else:
            self.sidebar.status_banner.show_warning("Wizard Live complete.")
        self._sync_wizard_live_session_from_disk()
        self.refresh_project()
        self.refresh_chat()
        self._drain_pending_wizard_live_action()

    def _on_wizard_live_failed(self, error: str) -> None:
        self._wizard_live_running = False
        self.sidebar.status_banner.show_error(f"Wizard Live error: {error}")
        self._sync_wizard_live_session_from_disk()
        self._drain_pending_wizard_live_action()

    def _handle_wizard_live_command(self, command: str, body: str) -> None:
        if not self.current_project_id:
            return
        if command == "stop":
            self._queue_wizard_live_action(
                mode="stop",
                trigger="wizard_live_stop_command",
                operator_message=body,
                include_full_intake=False,
                repo_path=None,
            )
            return

        repo_path = self._resolve_wizard_live_repo_path(allow_picker=True)
        if repo_path is None:
            self.sidebar.status_banner.show_error("Wizard Live requires a repo path.")
            return
        self._wizard_live_repo_path = repo_path

        if command == "start":
            self._queue_wizard_live_action(
                mode="start",
                trigger="wizard_live_start_command",
                operator_message=body,
                include_full_intake=True,
                repo_path=repo_path,
            )
            return

        include_full_intake = not self._wizard_live_session_active
        self._queue_wizard_live_action(
            mode="run",
            trigger="wizard_live_run_command",
            operator_message=body,
            include_full_intake=include_full_intake,
            repo_path=repo_path,
        )

    def _autokick_wizard_live(self, *, source: str, repo_path: Path | None) -> None:
        if not self.current_project_id:
            return
        if repo_path is None:
            return
        if self._wizard_live_session_active:
            return
        self._wizard_live_repo_path = repo_path
        trigger = f"wizard_live_autokick_{source}"
        message = f"auto kickoff from {source}"
        self._queue_wizard_live_action(
            mode="start",
            trigger=trigger,
            operator_message=message,
            include_full_intake=True,
            repo_path=repo_path,
        )

    def _confirm_takeover_wizard(self) -> bool:
        msg = (
            "Run Takeover Wizard headless?\n\n"
            "- Runs 1x openrouter exec (read-only sandbox)\n"
            "- Generates BMAD docs + L1 roundtable into this project\n"
            "- May consume credits\n"
        )
        choice = QMessageBox.question(
            self,
            "Takeover Wizard",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return choice == QMessageBox.Yes

    def _maybe_trigger_takeover_wizard(self, text: str, tags: list[str]) -> None:
        lowered = (text or "").lower()
        triggered = False
        if "wizard" in (tags or []):
            triggered = True
        if re.search(r"\blance\s+le\s+wizard\b", lowered):
            triggered = True
        if re.search(r"\blaunch\s+wizard\b", lowered):
            triggered = True
        if not triggered:
            return
        self.on_takeover_wizard_clicked()

    def on_takeover_wizard_clicked(self) -> None:
        if self._block_if_api_strict("takeover_wizard"):
            return
        if not self.current_project_id:
            return
        if self._takeover_wizard_running:
            self.sidebar.status_banner.show_warning("Takeover Wizard already running.")
            return

        repo_path = self._linked_repo_path()
        if repo_path is None:
            folder = QFileDialog.getExistingDirectory(self, "Select repo folder for takeover")
            if not folder:
                return
            repo_path = Path(folder)
            settings = self._load_settings_json(self.current_project_id)
            settings["linked_repo_path"] = str(repo_path.expanduser())
            self._save_settings_json(self.current_project_id, settings)

        if not self._confirm_takeover_wizard():
            return

        self._takeover_wizard_running = True

        def _worker() -> None:
            self._takeover_signals.started.emit(f"Starting wizard for {repo_path} ...")
            try:
                result = run_takeover_wizard(
                    projects_root=PROJECTS_DIR,
                    project_id=self.current_project_id,
                    repo_path=repo_path,
                    run_intake=True,
                    headless=True,
                )
            except Exception as exc:  # noqa: BLE001
                self._takeover_signals.failed.emit(str(exc))
                return
            self._takeover_signals.finished.emit(result)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_takeover_wizard_started(self, msg: str) -> None:
        self.sidebar.status_banner.show_warning(msg)

    def _on_takeover_wizard_finished(self, result: object) -> None:
        self._takeover_wizard_running = False
        if isinstance(result, TakeoverWizardResult):
            self.sidebar.status_banner.dismiss()
            self.sidebar.status_banner.show_warning(f"Wizard complete: {result.run_id}")
            repo_path = Path(result.repo_path).expanduser() if result.repo_path else None
            if result.status == "ok" and repo_path is not None:
                self._autokick_wizard_live(source="takeover", repo_path=repo_path)
        else:
            self.sidebar.status_banner.dismiss()
            self.sidebar.status_banner.show_warning("Wizard complete.")
        self.refresh_project()
        self.refresh_chat()

    def _on_takeover_wizard_failed(self, error: str) -> None:
        self._takeover_wizard_running = False
        self.sidebar.status_banner.show_error(f"Takeover Wizard failed: {error}")

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
        if self._block_if_api_strict("pack_light"):
            return
        if not self.current_project_id:
            return
        content = build_pack_context(self.current_project_id, "light", None)
        path = write_pack_context(self.current_project_id, "light", content)
        QApplication.clipboard().setText(content)
        self._emit_pack_feedback("Light", str(path))

    def on_pack_full(self) -> None:
        if self._block_if_api_strict("pack_full"):
            return
        if not self.current_project_id:
            return
        thread_tag = self.chatroom.current_thread_tag()
        content = build_pack_context(self.current_project_id, "full", thread_tag or None)
        path = write_pack_context(self.current_project_id, "full", content)
        QApplication.clipboard().setText(content)
        self._emit_pack_feedback("Full", str(path))

    def on_ping_agents(self) -> None:
        if self._block_if_api_strict("ping_agents"):
            return
        if not self.current_project_id:
            return
        context_ref = self.chatroom.consume_context_ref()
        text = "Ping @leo @victor @nova #ping"
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
        if context_ref:
            payload["context_ref"] = context_ref
        append_chat_message(self.current_project_id, payload)
        for tag in tags:
            append_thread_message(self.current_project_id, tag, payload)
        record_mentions(self.current_project_id, payload)
        self.run_auto_mode_tick()
        self._auto_reply(payload)
        self.refresh_chat()

    def _settings_path(self, project_id: str) -> Path:
        return project_dir(project_id) / "settings.json"

    def _default_llm_profile(self) -> dict:
        return {
            "voice_stt_model": "google/gemini-2.5-flash",
            "provider": "openrouter",
            "clems_model": "moonshotai/kimi-k2.5",
            "clems_catalog": [
                "moonshotai/kimi-k2.5",
                "anthropic/claude-sonnet-4.6",
                "anthropic/claude-opus-4.6",
            ],
            "l1_models": {
                "victor": "moonshotai/kimi-k2.5",
                "leo": "moonshotai/kimi-k2.5",
                "nova": "moonshotai/kimi-k2.5",
                "vulgarisation": "moonshotai/kimi-k2.5",
            },
            "l1_catalog": [
                "moonshotai/kimi-k2.5",
                "anthropic/claude-sonnet-4.6",
                "anthropic/claude-opus-4.6",
                "openai/gpt-5.4",
                "google/gemini-3.1-pro-preview",
                "x-ai/grok-4",
            ],
            "l2_default_model": "minimax/minimax-m2.5",
            "l2_pool": [
                "minimax/minimax-m2.5",
                "moonshotai/kimi-k2.5",
                "deepseek/deepseek-chat-v3.1",
            ],
            "l2_selection_mode": "manual_primary",
            "lfm_spawn_max": 10,
            "stream_enabled": True,
        }

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

    def _archive_ping_messages_once(self) -> None:
        if self.agent_ping_reminders_enabled:
            return
        if not self.current_project_id:
            return
        if self.current_project_id in self._ping_archive_done_projects:
            return
        self._ping_archive_done_projects.add(self.current_project_id)
        try:
            summary = archive_ping_reminders(self.current_project_id, bucket="bain")
        except Exception:
            return
        archived_count = int(summary.get("archived_count") or 0)
        if archived_count <= 0:
            return
        archive_path = str(summary.get("archive_path") or "").strip() or "chat/bain"
        self.sidebar.status_banner.show_warning(
            f"Archived {archived_count} ping reminders -> {archive_path}"
        )

    def refresh_model_routing_from_settings(self) -> None:
        if not self.current_project_id:
            return
        if self.api_strict_mode:
            try:
                payload = api_get_llm_profile(self.current_project_id)
            except Exception:
                payload = self._default_llm_profile()
            self.model_routing.set_profile_payload(payload)
            return
        settings = self._load_settings_json(self.current_project_id)
        profile = settings.get("llm_profile") if isinstance(settings.get("llm_profile"), dict) else {}
        payload = dict(self._default_llm_profile())
        payload.update(profile)
        self.model_routing.set_profile_payload(payload)

    def on_load_model_routing(self) -> None:
        if not self.current_project_id:
            return
        if not self.api_strict_mode:
            self.refresh_model_routing_from_settings()
            self.sidebar.status_banner.show_warning("Model routing loaded from local settings.")
            return
        try:
            payload = api_get_llm_profile(self.current_project_id)
        except Exception as exc:  # noqa: BLE001
            self.sidebar.status_banner.show_error(f"Load model routing failed: {exc}")
            return
        self.model_routing.set_profile_payload(payload)
        self.sidebar.status_banner.show_warning("Model routing loaded from API.")

    def on_save_model_routing(self) -> None:
        if not self.current_project_id:
            return
        payload = self.model_routing.profile_payload()
        if self.api_strict_mode:
            try:
                saved = api_put_llm_profile(self.current_project_id, payload)
            except Exception as exc:  # noqa: BLE001
                self.sidebar.status_banner.show_error(f"Save model routing failed: {exc}")
                return
            self.model_routing.set_profile_payload(saved)
            self.sidebar.status_banner.show_warning("Model routing saved to API.")
            return

        settings = self._load_settings_json(self.current_project_id)
        settings["llm_profile"] = payload
        self._save_settings_json(self.current_project_id, settings)
        self.sidebar.status_banner.show_warning("Model routing saved in local settings.")

    def refresh_pixel_feed(self, *_args: object) -> None:
        if not self.current_project_id:
            return
        window = self.pixel_view.selected_window()
        try:
            if self.api_strict_mode:
                payload = api_get_pixel_feed(self.current_project_id, window=window)
            else:
                payload = build_local_pixel_feed(self.current_project_id, window=window)
        except Exception as exc:  # noqa: BLE001
            self.pixel_view.status_label.setText(f"Pixel feed error: {exc}")
            return
        self.pixel_view.set_feed(payload)

    def _sync_auto_mode_from_settings(self, project: ProjectData) -> None:
        if self.api_strict_mode:
            self.auto_mode_enabled = False
            self.auto_send_enabled = False
            self.sidebar.auto_mode.set_enabled(False)
            self.sidebar.auto_mode.set_auto_send_enabled(False)
            if self.auto_mode_timer.isActive():
                self.auto_mode_timer.stop()
            return
        # Read settings from loaded project (fast path).
        settings = project.settings if isinstance(project.settings, dict) else {}
        feature_flags = settings.get("feature_flags") if isinstance(settings.get("feature_flags"), dict) else {}
        enabled = feature_flags.get("auto_mode")
        if enabled is None:
            enabled = True

        auto_mode = settings.get("auto_mode") if isinstance(settings.get("auto_mode"), dict) else {}
        interval_seconds = auto_mode.get("interval_seconds", 5)
        max_actions = auto_mode.get("max_actions", 1)
        auto_send_enabled = auto_mode.get("auto_send_enabled")
        if auto_send_enabled is None:
            auto_send_enabled = feature_flags.get("auto_send")
        if auto_send_enabled is None:
            auto_send_enabled = False

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
        self.auto_send_enabled = bool(auto_send_enabled)

        self.sidebar.auto_mode.set_enabled(self.auto_mode_enabled)
        self.sidebar.auto_mode.set_auto_send_enabled(self.auto_send_enabled)
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
        feature_flags["auto_send"] = bool(self.auto_send_enabled)

        auto_mode = settings.get("auto_mode")
        if not isinstance(auto_mode, dict):
            auto_mode = {}
            settings["auto_mode"] = auto_mode
        auto_mode["interval_seconds"] = int(self.auto_mode_interval_seconds)
        auto_mode["max_actions"] = int(self.auto_mode_max_actions)
        auto_mode["auto_send_enabled"] = bool(self.auto_send_enabled)

        self._save_settings_json(self.current_project_id, settings)

    def on_auto_mode_toggled(self, enabled: bool) -> None:
        if self._block_if_api_strict("auto_mode_toggle"):
            self.sidebar.auto_mode.set_enabled(False)
            return
        self.auto_mode_enabled = bool(enabled)
        self._persist_auto_mode_settings()
        if self.auto_mode_enabled:
            self.auto_mode_timer.start()
            self.run_auto_mode_tick(manual=True)
        else:
            self.auto_mode_timer.stop()
        self.sidebar.auto_mode.set_last_error("")

    def on_auto_mode_run_once(self) -> None:
        if self._block_if_api_strict("auto_mode_run_once"):
            return
        self.run_auto_mode_tick(manual=True)

    def on_auto_send_toggled(self, enabled: bool) -> None:
        if self._block_if_api_strict("auto_send_toggle"):
            self.sidebar.auto_mode.set_auto_send_enabled(False)
            return
        self.auto_send_enabled = bool(enabled)
        self._persist_auto_mode_settings()
        self.sidebar.auto_mode.set_last_error("")

    def run_auto_mode_tick(self, manual: bool = False) -> None:
        if self.api_strict_mode:
            return
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

        # Apply at most max_actions actions (already capped).
        for action in result.actions:
            QApplication.clipboard().setText(action.prompt_text)
            now = datetime.now().strftime("%H:%M:%S")
            auto_send_error = ""
            if self.auto_send_enabled:
                route = SendRoute(
                    project_id=self.current_project_id,
                    agent_id=action.agent_id,
                    platform=action.platform,
                    app_name=action.app_to_open,
                    window_title_contains="",
                    require_window_match=False,
                )
                send_result = send_action(action, route, dry_run=False)
                if send_result.sent:
                    self.sidebar.auto_mode.set_last_error("")
                    self.sidebar.auto_mode.set_last_dispatch(f"{now} sent @{action.agent_id} -> {send_result.app_name}")
                    continue
                err = (send_result.error or send_result.status or "auto-send failed").strip()
                hint = ""
                if send_result.status == "permission_denied":
                    hint = " (check macOS Accessibility permissions)"
                auto_send_error = f"Auto-send {send_result.status}: {err}{hint}"
                self.sidebar.auto_mode.set_last_error(auto_send_error)

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
                if not auto_send_error:
                    self.sidebar.auto_mode.set_last_error("")
            self.sidebar.auto_mode.set_last_dispatch(f"{now} @{action.agent_id} -> {action.app_to_open}")

        # If there was dispatch activity but no action (max_actions=0), still update status.
        if not result.actions and result.dispatched_count:
            now = datetime.now().strftime("%H:%M:%S")
            self.sidebar.auto_mode.set_last_dispatch(f"{now} dispatched {result.dispatched_count}")

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

    def _build_project_context(self) -> str:
        """Build a compact project state context string for the LLM."""
        phase, objective, next_items, eta = self._read_state_summary()
        lines: list[str] = []
        if phase:
            lines.append(f"Phase: {phase}")
        if objective:
            lines.append(f"Objectif: {objective}")
        if eta:
            lines.append(f"ETA: {eta}")
        if next_items:
            lines.append("Prochaines etapes: " + ", ".join(next_items[:5]))
        lines.append(f"Projet: {self.current_project_id}")
        lines.append(f"Data dir: {PROJECTS_DIR}")
        return "\n".join(lines)

    def _auto_reply(self, payload: dict) -> None:
        """Send operator message to LLM for AI response (async)."""
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
        message_id = payload.get("message_id", "")

        # Show typing indicator
        self.chatroom.show_typing()
        self.chatroom.set_status("Clems réfléchit...")

        # Build project context for the LLM
        project_context = self._build_project_context()

        # Fire async LLM call
        signals = self._llm_chat_signals
        llm_send_async(
            text,
            project_context=project_context,
            on_success=lambda resp: signals.response_ready.emit(resp, message_id),
            on_error=lambda err: signals.error.emit(err),
        )

    def _on_llm_chat_response(self, response_text: str, reply_to_id: str) -> None:
        """Handle LLM response on main thread (via signal)."""
        self.chatroom.hide_typing()
        self.chatroom.set_status("")

        reply = {
            "message_id": self._make_message_id("clems"),
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "clems",
            "text": response_text,
            "tags": [],
            "mentions": [],
            "event": "clems_llm_reply",
            "reply_to": reply_to_id,
        }
        append_chat_message(self.current_project_id, reply)
        self.refresh_chat()

    def _on_llm_chat_error(self, error: str) -> None:
        """Handle LLM error on main thread."""
        self.chatroom.hide_typing()
        self.chatroom.set_status("")

        reply = {
            "message_id": self._make_message_id("clems"),
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "clems",
            "text": f"⚠️ Erreur: {error}",
            "tags": [],
            "mentions": [],
            "event": "clems_error",
        }
        append_chat_message(self.current_project_id, reply)
        self.refresh_chat()

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

        # Agent reminders (run requests) are opt-in to avoid ping loops.
        if self.agent_ping_reminders_enabled:
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

    def _toggle_sidebar_visibility(self, checked: bool) -> None:
        self.sidebar.setVisible(checked)
        if checked:
            self.toggle_sidebar_btn.setStyleSheet("color: #5E6167; font-weight: bold; border: none;")
        else:
            self.toggle_sidebar_btn.setStyleSheet("color: #B91C1C; font-weight: bold; border: none;")

    def _toggle_chat_visibility(self, checked: bool) -> None:
        self.chatroom.setVisible(checked)
        if checked:
            self.toggle_chat_btn.setStyleSheet("color: #5E6167; font-weight: bold; border: none;")
        else:
            self.toggle_chat_btn.setStyleSheet("color: #B91C1C; font-weight: bold; border: none;")
