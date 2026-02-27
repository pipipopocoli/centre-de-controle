from __future__ import annotations

import json
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
from app.services.pack_context import build_pack_context, write_pack_context
from app.services.auto_mode import dispatch_once as auto_mode_dispatch_once
from app.services.auto_send import SendRoute, send_action
from app.services.takeover_wizard import TakeoverWizardResult, run_takeover_wizard
from app.ui.agents_grid import AgentsGridWidget
from app.ui.chatroom import ChatroomWidget
from app.ui.doc_viewer import DocsViewerWidget
from app.ui.project_bible import ProjectBibleWidget
from app.ui.project_pilotage import ProjectPilotageWidget
from app.ui.roadmap import RoadmapWidget
from app.ui.sidebar import SidebarWidget


class TakeoverWizardSignals(QObject):
    started = Signal(str)
    finished = Signal(object)
    failed = Signal(str)


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
        title = "Centre de controle"
        if version_text:
            title = f"{title} - {version_text}"
        self.setWindowTitle(title)
        self.resize(1400, 860)
        self.current_project_id = project.project_id
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
        self.auto_mode_codex_app = "Codex"
        self.auto_mode_ag_app = "Antigravity"
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
        self.run_auto_mode_tick()

        self.project_refresh_timer = QTimer(self)
        self.project_refresh_timer.setInterval(5000)
        self.project_refresh_timer.timeout.connect(self.refresh_project)
        self.project_refresh_timer.start()

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
        self.reminder_timer.start()

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

    def refresh_project(self) -> None:
        if not self.current_project_id:
            return
        project = load_project(self.current_project_id)
        self.load_project(project, refresh_chat_now=False, force_portfolio_refresh=False)
        self.refresh_bible(force=False)

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
        # Auto-mode should react quickly to operator mentions (when enabled).
        self.run_auto_mode_tick()
        self._maybe_trigger_takeover_wizard(text, tags)
        self._auto_reply(payload)
        self.chatroom.input.clear()
        self.refresh_chat()

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

    def _confirm_takeover_wizard(self) -> bool:
        msg = (
            "Run Takeover Wizard headless?\n\n"
            "- Runs 1x codex exec (read-only sandbox)\n"
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

    def on_auto_send_toggled(self, enabled: bool) -> None:
        self.auto_send_enabled = bool(enabled)
        self._persist_auto_mode_settings()
        self.sidebar.auto_mode.set_last_error("")

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
