"""Pilotage tab — clear operational dashboard with visual timeline.

Replaces the dense HTML view with native Qt widgets:
- Phase header with progress bar
- Now / Next / Blockers columns
- Visual timeline route (issues + state)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.data.model import ProjectData
from app.services.cost_telemetry import estimate_monthly_cad_from_path, legacy_monthly_cad_estimate
from app.services.live_activity_feed import build_live_activity_feed
from app.services.project_pilotage import build_portfolio_snapshot
from app.ui.project_timeline import ProjectTimelineWidget, _parse_state_items

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _detect_runtime_source(project_dir: Path) -> tuple[str, str]:
    repo_root = Path(__file__).resolve().parents[2] / "control" / "projects"
    appsupport_root = Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"
    try:
        resolved = project_dir.expanduser().resolve()
    except OSError:
        resolved = project_dir
    try:
        resolved.relative_to(appsupport_root)
        return "appsupport", str(appsupport_root)
    except ValueError:
        pass
    try:
        resolved.relative_to(repo_root)
        return "repo", str(repo_root)
    except ValueError:
        pass
    return "custom", str(resolved)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _status_bucket(status: str | None, blockers: list[str]) -> str:
    normalized = str(status or "").strip().lower()
    blockers_clean = [item.strip() for item in blockers if str(item).strip()]
    if blockers_clean and normalized in {"", "idle", "completed", "replied", "closed"}:
        return "blocked"
    if normalized in {"blocked", "error"}:
        return "blocked"
    if normalized in {"planning", "executing", "verifying"}:
        return "action"
    if normalized in {"pinged", "queued", "dispatched", "reminded", "waiting_reconfirm"}:
        return "waiting"
    return "rest"


PHASE_PROGRESS = {
    "plan": 10,
    "planning": 10,
    "implement": 25,
    "implementation": 25,
    "code": 25,
    "test": 50,
    "testing": 50,
    "qa": 50,
    "review": 75,
    "validation": 75,
    "verify": 75,
    "ship": 90,
    "deploy": 90,
    "deploiement": 90,
    "release": 95,
    "done": 100,
}


def _phase_percent(phase: str) -> int:
    return PHASE_PROGRESS.get(phase.strip().lower(), 10)


# -------------------------------------------------------------------
# List column widget (Now / Next / Blockers)
# -------------------------------------------------------------------
class _InfoColumn(QFrame):
    item_selected = Signal(str)

    def __init__(self, title: str, emoji: str, color: str) -> None:
        super().__init__()
        self.setObjectName("pilotageInfoColumn")
        self.setStyleSheet(f"""
            QFrame#pilotageInfoColumn {{
                background: #FFFFFF;
                border: 1px solid #D9D3C8;
                border-radius: 8px;
                border-top: 3px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QLabel(f"{emoji} {title}")
        header.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {color};")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setObjectName("pilotageColumnList")
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QListWidget.SingleSelection)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list, 1)

    def set_items(self, items: list[str]) -> None:
        self._list.clear()
        if not items:
            placeholder = QListWidgetItem("Aucun")
            placeholder.setFlags(Qt.NoItemFlags)
            self._list.addItem(placeholder)
            return
        for item in items[:8]:
            text = item.strip()
            if len(text) > 120:
                text = text[:117] + "..."
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, item.strip())
            self._list.addItem(list_item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        value = str(item.data(Qt.UserRole) or "").strip()
        if not value:
            return
        self.item_selected.emit(value)


# -------------------------------------------------------------------
# Main widget
# -------------------------------------------------------------------
class ProjectPilotageWidget(QFrame):
    project_selected = Signal(str)
    mode_changed = Signal(str)
    scope_changed = Signal(str)
    context_selected = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("projectPilotage")
        self._project: ProjectData | None = None
        self._portfolio: list[ProjectData] = []
        self._mode = "simple"
        self._scope = "project"
        self._portfolio_throttle_seconds = 10
        self._portfolio_cache_html = ""
        self._portfolio_cache_at: datetime | None = None
        self._state_source_path: Path | None = None
        self._live_code_cache: dict | None = None
        self._live_code_at: datetime | None = None
        self._live_code_refresh_seconds = 15
        self._live_repo_path = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # ── Header bar ──────────────────────────────────────────────
        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(8)

        self._title = QLabel("Pilotage")
        self._title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1C1C1C;")
        h_lay.addWidget(self._title, 1)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setObjectName("pilotageActionButton")
        self.refresh_btn.clicked.connect(lambda: self.refresh_content(force=True))
        h_lay.addWidget(self.refresh_btn)

        self.mode_btn = QPushButton("Mode: Simple")
        self.mode_btn.setObjectName("pilotageActionButton")
        self.mode_btn.clicked.connect(self._toggle_mode)
        h_lay.addWidget(self.mode_btn)

        self.scope_btn = QPushButton("Scope: Projet")
        self.scope_btn.setObjectName("pilotageActionButton")
        self.scope_btn.clicked.connect(self._toggle_scope)
        h_lay.addWidget(self.scope_btn)

        self.auto_badge = QLabel("Auto 5s")
        self.auto_badge.setObjectName("pilotageModeBadge")
        h_lay.addWidget(self.auto_badge)


        root.addWidget(header)

        # ── Phase bar ───────────────────────────────────────────────
        phase_frame = QFrame()
        phase_frame.setObjectName("pilotagePhaseFrame")
        phase_frame.setStyleSheet("""
            QFrame#pilotagePhaseFrame {
                background: #FFFFFF;
                border: 1px solid #D9D3C8;
                border-radius: 8px;
            }
        """)
        phase_lay = QVBoxLayout(phase_frame)
        phase_lay.setContentsMargins(14, 10, 14, 10)
        phase_lay.setSpacing(6)

        phase_row = QHBoxLayout()
        self._phase_label = QLabel("Phase: —")
        self._phase_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #2C5DFF;")
        phase_row.addWidget(self._phase_label)
        phase_row.addStretch(1)
        self._phase_pct = QLabel("")
        self._phase_pct.setStyleSheet("font-size: 12px; color: #5E6167; font-family: Menlo, monospace;")
        phase_row.addWidget(self._phase_pct)
        phase_lay.addLayout(phase_row)

        self._objective_label = QLabel("")
        self._objective_label.setWordWrap(True)
        self._objective_label.setStyleSheet("font-size: 12px; color: #5E6167;")
        phase_lay.addWidget(self._objective_label)

        self._progress = QProgressBar()
        self._progress.setObjectName("pilotageProgress")
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar { background: #E8E2D9; border: none; border-radius: 4px; }
            QProgressBar::chunk { background: #2C5DFF; border-radius: 4px; }
        """)
        phase_lay.addWidget(self._progress)

        root.addWidget(phase_frame)

        self._health_line = QLabel("SLO: n/a | Cost CAD: n/a")
        self._health_line.setObjectName("pilotageHealthLine")
        self._health_line.setStyleSheet(
            "padding: 6px 10px; background: #FFFFFF; border: 1px solid #D9D3C8; border-radius: 8px; "
            "font-size: 12px; color: #1C1C1C;"
        )
        self._health_line.setWordWrap(True)
        root.addWidget(self._health_line)

        # ── Now / Next / Blockers ───────────────────────────────────
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(10)
        self._col_now = _InfoColumn("Maintenant", "⚡", "#2C5DFF")
        self._col_next = _InfoColumn("Prochain", "➡️", "#0F766E")
        self._col_blockers = _InfoColumn("Blockers", "🚧", "#C94B4B")
        self._col_now.item_selected.connect(lambda text: self._emit_state_context("state_item", "now", text))
        self._col_next.item_selected.connect(lambda text: self._emit_state_context("state_item", "next", text))
        self._col_blockers.item_selected.connect(lambda text: self._emit_state_context("state_item", "blocker", text))
        cols_layout.addWidget(self._col_now, 1)
        cols_layout.addWidget(self._col_next, 1)
        cols_layout.addWidget(self._col_blockers, 1)
        root.addLayout(cols_layout)

        # ── Live view (task + code + agents) ───────────────────────
        self._live_frame = QFrame()
        self._live_frame.setObjectName("pilotageLiveFrame")
        live_layout = QHBoxLayout(self._live_frame)
        live_layout.setContentsMargins(0, 0, 0, 0)
        live_layout.setSpacing(10)

        self._live_code_col = _InfoColumn("Code now", "🧪", "#7C3AED")
        self._live_tasks_col = _InfoColumn("Tasks now", "📋", "#2C5DFF")
        self._live_agents_col = _InfoColumn("Agents now", "👥", "#0F766E")

        self._live_code_col.item_selected.connect(lambda text: self._emit_live_context("code_change", text))
        self._live_tasks_col.item_selected.connect(lambda text: self._emit_live_context("task_item", text))
        self._live_agents_col.item_selected.connect(lambda text: self._emit_live_context("agent_live", text))

        live_layout.addWidget(self._live_code_col, 1)
        live_layout.addWidget(self._live_tasks_col, 1)
        live_layout.addWidget(self._live_agents_col, 1)
        root.addWidget(self._live_frame)

        # ── Timeline route ──────────────────────────────────────────
        self._timeline = ProjectTimelineWidget()
        self._timeline.context_selected.connect(self.context_selected.emit)
        root.addWidget(self._timeline, 1)

    # ── Public API (keep backward compat with MainWindow) ──────────
    @property
    def mode(self) -> str:
        return self._mode

    @property
    def scope(self) -> str:
        return self._scope

    def set_throttle_seconds(self, seconds: int) -> None:
        try:
            value = int(seconds)
        except (TypeError, ValueError):
            value = 10
        self._portfolio_throttle_seconds = max(1, min(value, 120))

    def set_project(self, project: ProjectData, portfolio: list[ProjectData], *, refresh: bool = False) -> None:
        previous_id = self._project.project_id if self._project is not None else ""
        self._project = project
        self._portfolio = list(portfolio)
        self._title.setText(f"Pilotage — {project.name}")

        if previous_id != project.project_id:
            self._portfolio_cache_html = ""
            self._portfolio_cache_at = None

        if refresh or previous_id != project.project_id:
            self.refresh_content(force=True)

    def set_mode(self, mode: str, *, emit_signal: bool = False) -> None:
        normalized = str(mode or "simple").strip().lower()
        if normalized not in {"simple", "tech"}:
            normalized = "simple"
        if self._mode == normalized:
            self._update_mode_label()
            return
        self._mode = normalized
        self._update_mode_label()
        if emit_signal:
            self.mode_changed.emit(self._mode)
        self.refresh_content(force=True)

    def set_scope(self, scope: str, *, emit_signal: bool = False) -> None:
        normalized = str(scope or "project").strip().lower()
        if normalized not in {"project", "portfolio"}:
            normalized = "project"
        if self._scope == normalized:
            self._update_scope_label()
            return
        self._scope = normalized
        self._update_scope_label()
        if emit_signal:
            self.scope_changed.emit(self._scope)
        self.refresh_content(force=True)

    def refresh_content(self, *, force: bool = False) -> None:
        if self._project is None:
            return

        project_dir = self._project.path
        state_path = project_dir / "STATE.md"
        self._state_source_path = state_path
        state = _parse_state_items(state_path)
        runtime_source, runtime_root = _detect_runtime_source(project_dir)

        # Phase
        phase_items = state.get("Phase", [])
        phase = phase_items[0] if phase_items else "Plan"
        pct = _phase_percent(phase)
        self._phase_label.setText(f"Phase: {phase}")
        self._phase_pct.setText(f"{pct}%")
        self._phase_pct.setVisible(self._mode == "tech")
        self.auto_badge.setVisible(self._mode == "tech")
        self._progress.setValue(pct)

        # Objective
        obj_items = state.get("Objective", [])
        obj = obj_items[0] if obj_items else ""
        self._objective_label.setText(f"Cible: {obj}" if obj else "")

        slo_path = project_dir / "runs" / "slo_verdict_latest.json"
        slo_verdict = "n/a"
        if slo_path.exists():
            try:
                slo_payload = json.loads(_read_text(slo_path))
            except Exception:
                slo_payload = {}
            if isinstance(slo_payload, dict):
                slo_verdict = str(slo_payload.get("verdict") or "n/a")

        cost_path = project_dir / "runs" / "cost_events.ndjson"
        monthly_cost, monthly_event_count = estimate_monthly_cad_from_path(cost_path, now_utc=datetime.now(timezone.utc))
        if monthly_event_count > 0:
            monthly_cost_label = f"{monthly_cost:.2f}"
        else:
            legacy_costs_path = project_dir / "vulgarisation" / "costs.json"
            legacy_payload: dict | None = None
            if legacy_costs_path.exists():
                try:
                    parsed = json.loads(_read_text(legacy_costs_path))
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    legacy_payload = parsed
            legacy_cost = legacy_monthly_cad_estimate(legacy_payload)
            monthly_cost_label = "n/a" if legacy_cost is None else f"{legacy_cost:.2f}"

        level_counts = {0: 0, 1: 0, 2: 0}
        level_buckets = {
            0: {"action": 0, "waiting": 0, "blocked": 0},
            1: {"action": 0, "waiting": 0, "blocked": 0},
            2: {"action": 0, "waiting": 0, "blocked": 0},
        }
        for agent in self._project.agents:
            try:
                level = int(agent.level)
            except (TypeError, ValueError):
                level = 2
            level = level if level in {0, 1, 2} else 2
            level_counts[level] += 1
            bucket = _status_bucket(agent.status, agent.blockers)
            if bucket in {"action", "waiting", "blocked"}:
                level_buckets[level][bucket] += 1

        settings_payload = self._project.settings if isinstance(self._project.settings, dict) else {}
        control_gates = settings_payload.get("control_gates") if isinstance(settings_payload.get("control_gates"), dict) else {}
        pulse_stale_seconds = int(control_gates.get("pulse_stale_seconds") or 3600)
        auto_mode_state_path = project_dir / "runs" / "auto_mode_state.json"
        pulse_status = "unknown"
        if auto_mode_state_path.exists():
            try:
                state_payload = json.loads(_read_text(auto_mode_state_path))
            except Exception:
                state_payload = {}
            counters = state_payload.get("counters") if isinstance(state_payload.get("counters"), dict) else {}
            pulse_at = _parse_iso(
                str(counters.get("last_pulse_at") or counters.get("dispatch_last_at") or counters.get("last_tick_at") or "")
            )
            if pulse_at is None:
                pulse_status = "stale"
            else:
                pulse_age = max(int((datetime.now(timezone.utc) - pulse_at).total_seconds()), 0)
                pulse_status = "ok" if pulse_age <= max(pulse_stale_seconds, 60) else "stale"

        if self._scope == "portfolio" and self._portfolio:
            snapshot = build_portfolio_snapshot(self._portfolio)
            self._title.setText("Pilotage — Portfolio")
            self._health_line.setText(
                f"Projects: {int(snapshot.get('projects_count', 0))} | "
                f"Blockers: {int(snapshot.get('total_blockers', 0))} | "
                f"Active agents: {int(snapshot.get('total_active_agents', 0))} | "
                f"Data root: {runtime_source} | Pulse: {pulse_status}"
            )

            now_items = [
                f"Focus: {self._project.project_id}",
                f"SLO: {slo_verdict}",
                f"Cost CAD (month): {monthly_cost_label}",
            ]
            next_items: list[str] = []
            blockers_items: list[str] = []
            rows = snapshot.get("rows") if isinstance(snapshot.get("rows"), list) else []
            for row in rows[:5]:
                if not isinstance(row, dict):
                    continue
                pid = str(row.get("project_id") or "-")
                risk = str(row.get("dominant_risk") or "-")
                done_pct = int(row.get("done_pct") or 0)
                blockers = int(row.get("blockers") or 0)
                next_items.append(f"{pid}: done={done_pct}% risk={risk}")
                if blockers > 0:
                    blockers_items.append(f"{pid}: {blockers} blockers")

            self._col_now.set_items(now_items)
            self._col_next.set_items(next_items)
            self._col_blockers.set_items(blockers_items or ["No blockers"])
        else:
            self._title.setText(f"Pilotage — {self._project.name}")

            # Health line logic
            vulg_snapshot_path = project_dir / "vulgarisation" / "snapshot.json"
            vulg_generated_at = "n/a"
            vulg_freshness = "n/a"
            if vulg_snapshot_path.exists():
                try:
                    vulg_payload = json.loads(_read_text(vulg_snapshot_path))
                except Exception:
                    vulg_payload = {}
                if isinstance(vulg_payload, dict):
                    vulg_generated_at = str(vulg_payload.get("generated_at") or "n/a")
                    freshness_payload = vulg_payload.get("freshness")
                    if isinstance(freshness_payload, dict):
                        vulg_freshness = str(freshness_payload.get("status") or "n/a")

            if self._mode == "simple":
                # High-level summary
                slo_status = "OK" if slo_verdict == "GO" else ("WARN" if slo_verdict == "HOLD" else "N/A")
                cost_status = "OK" if monthly_cost_label != "n/a" else "WARN"
                self._health_line.setText(
                    f"Status: SLO={slo_status} | Cost={cost_status} | Data={runtime_source} | "
                    f"Vulgarisation={vulg_freshness} | Pulse={pulse_status} | "
                    f"L0={level_counts[0]} L1={level_counts[1]} L2={level_counts[2]}"
                )
            else:
                self._health_line.setText(
                    f"SLO: {slo_verdict} | Cost CAD (month): {monthly_cost_label} | "
                    f"Data root [{runtime_source}]: {runtime_root} | Vulgarisation generated_at: {vulg_generated_at} | "
                    f"Pulse: {pulse_status} | "
                    f"L0(action {level_buckets[0]['action']}/attente {level_buckets[0]['waiting']}/bloque {level_buckets[0]['blocked']}) "
                    f"L1(action {level_buckets[1]['action']}/attente {level_buckets[1]['waiting']}/bloque {level_buckets[1]['blocked']}) "
                    f"L2(action {level_buckets[2]['action']}/attente {level_buckets[2]['waiting']}/bloque {level_buckets[2]['blocked']})"
                )

            # Lists
            now_list = state.get("Now", []) + state.get("In Progress", [])
            next_list = state.get("Next", [])
            blockers_list = state.get("Blockers", [])

            if self._mode == "simple":
                now_list = now_list[:3]
                next_list = next_list[:3]
                blockers_list = blockers_list[:3]

            self._col_now.set_items(now_list)
            self._col_next.set_items(next_list)
            self._col_blockers.set_items(blockers_list)

        self._timeline.set_context(
            self._project,
            portfolio=self._portfolio,
            scope=self._scope,
            mode=self._mode,
        )
        self._refresh_live_view(force=force)

    def _refresh_live_view(self, *, force: bool = False) -> None:
        if self._project is None:
            return

        now = datetime.now(timezone.utc)
        include_code = force
        if not include_code:
            if self._live_code_cache is None or self._live_code_at is None:
                include_code = True
            else:
                age = (now - self._live_code_at).total_seconds()
                include_code = age >= self._live_code_refresh_seconds

        feed = build_live_activity_feed(self._project, limit=30, include_code=include_code)
        code_payload = feed.get("code") if isinstance(feed.get("code"), dict) else {}
        if include_code:
            self._live_code_cache = code_payload
            self._live_code_at = now
        elif self._live_code_cache is not None:
            code_payload = self._live_code_cache

        tasks_payload = feed.get("tasks") if isinstance(feed.get("tasks"), dict) else {}
        agents_payload = feed.get("agents") if isinstance(feed.get("agents"), dict) else {}

        self._live_repo_path = str(code_payload.get("repo_path") or "")

        code_items: list[str] = []
        branch = str(code_payload.get("branch") or "unknown")
        code_items.append(f"branch: {branch}")
        commits = code_payload.get("commits") if isinstance(code_payload.get("commits"), list) else []
        for row in commits[:3]:
            if not isinstance(row, dict):
                continue
            sha = str(row.get("sha") or "")[:7]
            msg = str(row.get("message") or "n/a")
            code_items.append(f"{sha} {msg}")
        changed_files = code_payload.get("changed_files") if isinstance(code_payload.get("changed_files"), list) else []
        for path in changed_files[:3]:
            text = str(path).strip()
            if text:
                code_items.append(f"changed: {text}")
        self._live_code_col.set_items(code_items[:8] or ["No code activity"])

        task_items: list[str] = []
        phase = str(tasks_payload.get("phase") or "Plan")
        open_requests = int(tasks_payload.get("open_requests") or 0)
        issues_payload = tasks_payload.get("issues") if isinstance(tasks_payload.get("issues"), dict) else {}
        task_items.append(f"phase: {phase}")
        task_items.append(f"open requests: {open_requests}")
        task_items.append(f"issues open: {int(issues_payload.get('open_like') or 0)}")
        for row in (tasks_payload.get("now") if isinstance(tasks_payload.get("now"), list) else [])[:2]:
            if isinstance(row, str) and row.strip():
                task_items.append(f"now: {row.strip()}")
        for row in (tasks_payload.get("next") if isinstance(tasks_payload.get("next"), list) else [])[:2]:
            if isinstance(row, str) and row.strip():
                task_items.append(f"next: {row.strip()}")
        self._live_tasks_col.set_items(task_items[:8] or ["No task activity"])

        levels = agents_payload.get("levels") if isinstance(agents_payload.get("levels"), dict) else {}
        l0 = levels.get(0) if isinstance(levels.get(0), dict) else {}
        l1 = levels.get(1) if isinstance(levels.get(1), dict) else {}
        l2 = levels.get(2) if isinstance(levels.get(2), dict) else {}
        agent_items = [
            f"L0 a:{int(l0.get('action') or 0)} w:{int(l0.get('waiting') or 0)} b:{int(l0.get('blocked') or 0)}",
            f"L1 a:{int(l1.get('action') or 0)} w:{int(l1.get('waiting') or 0)} b:{int(l1.get('blocked') or 0)}",
            f"L2 a:{int(l2.get('action') or 0)} w:{int(l2.get('waiting') or 0)} b:{int(l2.get('blocked') or 0)}",
        ]
        active_agents = agents_payload.get("active_agents") if isinstance(agents_payload.get("active_agents"), list) else []
        for row in active_agents[:3]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("agent_id") or "")
            status = str(row.get("status") or row.get("bucket") or "")
            if name:
                agent_items.append(f"{name}: {status}")
        self._live_agents_col.set_items(agent_items[:8] or ["No agent activity"])

    def _emit_live_context(self, kind: str, text: str) -> None:
        source_path = ""
        source_uri = ""
        if kind == "code_change" and self._live_repo_path:
            source_path = self._live_repo_path
            try:
                source_uri = Path(self._live_repo_path).resolve().as_uri()
            except Exception:
                source_uri = ""
        elif self._state_source_path is not None:
            source_path = str(self._state_source_path)
            try:
                source_uri = self._state_source_path.resolve().as_uri()
            except Exception:
                source_uri = ""
        payload = {
            "kind": kind,
            "id": kind,
            "title": text,
            "source_path": source_path,
            "source_uri": source_uri,
            "selected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        self.context_selected.emit(payload)

    def _emit_state_context(self, kind: str, context_id: str, text: str) -> None:
        source_path = str(self._state_source_path) if self._state_source_path is not None else ""
        source_uri = ""
        if self._state_source_path is not None and self._state_source_path.exists():
            try:
                source_uri = self._state_source_path.resolve().as_uri()
            except Exception:
                source_uri = ""
        payload = {
            "kind": kind,
            "id": context_id,
            "title": text,
            "source_path": source_path,
            "source_uri": source_uri,
            "selected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        self.context_selected.emit(payload)

    def _toggle_mode(self) -> None:
        next_mode = "tech" if self._mode == "simple" else "simple"
        self.set_mode(next_mode, emit_signal=True)

    def _toggle_scope(self) -> None:
        next_scope = "portfolio" if self._scope == "project" else "project"
        self.set_scope(next_scope, emit_signal=True)

    def _update_mode_label(self) -> None:
        label = "Simple" if self._mode == "simple" else "Tech"
        self.mode_btn.setText(f"Mode: {label}")

    def _update_scope_label(self) -> None:
        label = "Projet" if self._scope == "project" else "Portefeuille"
        self.scope_btn.setText(f"Scope: {label}")
