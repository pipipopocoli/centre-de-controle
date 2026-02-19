from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.model import PHASES, AgentState, ProjectData

STATUS_ACTION = {"planning", "executing", "verifying"}
STATUS_WAITING = {"pinged", "queued", "dispatched", "reminded"}
STATUS_BLOCKED = {"blocked", "error", "failed", "timeout"}
STATUS_REST = {"idle", "completed", "replied", "closed"}
OPEN_REQUEST_STATUSES = {"queued", "dispatched", "reminded"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return default


def _safe_uri(path: Path) -> str:
    try:
        return path.resolve().as_uri()
    except Exception:
        return ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


def _resolve_linked_repo_path(settings: dict[str, Any]) -> Path | None:
    if not isinstance(settings, dict):
        return None
    for raw in (
        str(settings.get("linked_repo_path") or "").strip(),
        str(settings.get("repo_path") or "").strip(),
        str(settings.get("repo") or "").strip(),
    ):
        if not raw:
            continue
        path = Path(raw).expanduser()
        if path.exists() and path.is_dir():
            return path
    return None


def _extract_first_paragraph(path: Path) -> str:
    if not path.exists():
        return ""
    chunk: list[str] = []
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line:
            if chunk:
                break
            continue
        if line.startswith("#"):
            continue
        chunk.append(line)
        if len(" ".join(chunk)) >= 360:
            break
    return " ".join(chunk).strip()


def _parse_sections(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    if not path.exists():
        return sections
    current: str | None = None
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if not current:
            continue
        if line.startswith("- "):
            sections[current].append(line[2:].strip())
        elif re.match(r"^\d+\.\s+", line):
            sections[current].append(re.sub(r"^\d+\.\s+", "", line).strip())
    return sections


def _normalize_phase(phase: str) -> str:
    value = str(phase or "").strip().lower()
    if value in {"plan", "planning"}:
        return "Plan"
    if value in {"implement", "implementation", "code", "executing"}:
        return "Implement"
    if value in {"test", "testing", "qa"}:
        return "Test"
    if value in {"review", "validation", "verify", "verifying"}:
        return "Review"
    if value in {"ship", "release", "deploy", "deploiement", "completed", "done"}:
        return "Ship"
    for item in PHASES:
        if item.lower() == value:
            return item
    return "Plan"


def _phase_pct(phase: str) -> int:
    normalized = _normalize_phase(phase)
    idx = 0
    for i, item in enumerate(PHASES):
        if item == normalized:
            idx = i
            break
    return int((idx / max(len(PHASES) - 1, 1)) * 100)


def _normalize_issue_status(value: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"done", "closed", "completed", "ship"}:
        return "done"
    if raw in {"in progress", "in_progress", "active", "implement", "executing"}:
        return "in_progress"
    if raw in {"blocked", "error", "failed"}:
        return "blocked"
    return "todo"


def _issue_stats(project_dir: Path) -> dict[str, Any]:
    stats = {"todo": 0, "in_progress": 0, "blocked": 0, "done": 0, "total": 0, "done_pct": 0}
    issues_dir = project_dir / "issues"
    if not issues_dir.exists():
        return stats

    for issue_path in sorted(issues_dir.glob("ISSUE-*.md")):
        status = "todo"
        for raw in _read_text(issue_path).splitlines():
            line = raw.strip()
            if line.lower().startswith("- status:"):
                status = _normalize_issue_status(line.split(":", 1)[1].strip())
                break
        stats[status] += 1
        stats["total"] += 1

    total = max(stats["total"], 1)
    stats["done_pct"] = int((stats["done"] / total) * 100)
    return stats


def _normalize_agent_status(status: str | None) -> str:
    return str(status or "").strip().lower()


def _agent_stats(agents: list[AgentState]) -> dict[str, int]:
    counters = {"rest": 0, "action": 0, "waiting": 0, "blocked": 0, "active": 0, "total": len(agents)}
    for agent in agents:
        s = _normalize_agent_status(agent.status)
        if s in STATUS_BLOCKED:
            counters["blocked"] += 1
            counters["active"] += 1
        elif s in STATUS_WAITING:
            counters["waiting"] += 1
            counters["active"] += 1
        elif s in STATUS_ACTION:
            counters["action"] += 1
            counters["active"] += 1
        elif s in STATUS_REST or not s:
            counters["rest"] += 1
        else:
            counters["rest"] += 1
    return counters


def _pending_requests(project_dir: Path) -> int:
    path = project_dir / "runs" / "requests.ndjson"
    if not path.exists():
        return 0
    count = 0
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in OPEN_REQUEST_STATUSES:
            count += 1
    return count


def _state_bundle(project: ProjectData) -> dict[str, Any]:
    project_dir = project.path
    sections = _parse_sections(project_dir / "STATE.md")

    phase_items = sections.get("Phase") or [""]
    phase = _normalize_phase(phase_items[0] if phase_items else "")

    objective_items = sections.get("Objective") or []
    objective = objective_items[0] if objective_items else ""

    state_next = sections.get("Next") or []
    state_now = sections.get("Now") or []
    state_risks = sections.get("Risks") or []
    state_blockers = [
        item
        for item in (sections.get("Blockers") or [])
        if item.strip().lower() not in {"none", "n/a", "-"}
    ]
    gates = _dedupe((sections.get("Gates") or []) + (sections.get("Milestones") or []) + (sections.get("Checkpoints") or []))

    roadmap_next = project.roadmap.get("next", []) if isinstance(project.roadmap, dict) else []
    roadmap_risks = project.roadmap.get("risks", []) if isinstance(project.roadmap, dict) else []

    next_top = _dedupe(state_next + roadmap_next)[:5]
    risks = _dedupe(state_risks + roadmap_risks)

    return {
        "phase": phase,
        "phase_pct": _phase_pct(phase),
        "objective": objective,
        "now": state_now,
        "next_top": next_top,
        "risks": risks,
        "dominant_risk": risks[0] if risks else "-",
        "blockers": state_blockers,
        "blockers_count": len(state_blockers),
        "gates": gates[:6],
    }


def build_portfolio_snapshot(projects: list[ProjectData]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    phase_distribution = {phase: 0 for phase in PHASES}
    total_blockers = 0
    total_active_agents = 0

    for project in projects:
        state = _state_bundle(project)
        issue = _issue_stats(project.path)
        agent = _agent_stats(project.agents)

        blockers_count = max(state["blockers_count"], agent["blocked"])
        total_blockers += blockers_count
        total_active_agents += agent["active"]

        phase = state["phase"]
        if phase not in phase_distribution:
            phase_distribution[phase] = 0
        phase_distribution[phase] += 1

        rows.append(
            {
                "project_id": project.project_id,
                "project_name": project.name,
                "phase": phase,
                "phase_pct": state["phase_pct"],
                "done_pct": issue["done_pct"],
                "blockers": blockers_count,
                "active_agents": agent["active"],
                "dominant_risk": state["dominant_risk"],
            }
        )

    rows.sort(key=lambda item: (-int(item["blockers"]), int(item["done_pct"]), item["project_id"]))
    top_risks = rows[:6]

    return {
        "generated_at": _utc_now_iso(),
        "projects_count": len(rows),
        "total_blockers": total_blockers,
        "total_active_agents": total_active_agents,
        "phase_distribution": phase_distribution,
        "rows": rows,
        "top_risks": top_risks,
    }


def _render_list(items: list[str], fallback: str = "n/a") -> str:
    if not items:
        return f"<li>{html.escape(fallback)}</li>"
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def _svg_phase_distribution(distribution: dict[str, int]) -> str:
    width = 560
    height = 180
    bar_width = 70
    spacing = 34
    origin_x = 40
    origin_y = 150
    max_value = max(distribution.values()) if distribution else 1
    max_value = max(max_value, 1)

    bars: list[str] = []
    for idx, phase in enumerate(PHASES):
        value = int(distribution.get(phase, 0))
        h = int((value / max_value) * 90)
        x = origin_x + idx * (bar_width + spacing)
        y = origin_y - h
        bars.append(
            f"<rect x='{x}' y='{y}' width='{bar_width}' height='{h}' rx='6' fill='#2c5dff' />"
            f"<text x='{x + bar_width/2}' y='{origin_y + 16}' text-anchor='middle' font-size='11' fill='#5e6167'>{html.escape(phase)}</text>"
            f"<text x='{x + bar_width/2}' y='{y - 6}' text-anchor='middle' font-size='11' fill='#1c1c1c'>{value}</text>"
        )

    return (
        f"<svg viewBox='0 0 {width} {height}' width='100%' height='180' xmlns='http://www.w3.org/2000/svg'>"
        "<rect x='0' y='0' width='100%' height='100%' fill='#ffffff' rx='10'/>"
        "<line x1='30' y1='150' x2='540' y2='150' stroke='#d9d3c8' stroke-width='1'/>"
        + "".join(bars)
        + "</svg>"
    )


def _svg_top_risk(rows: list[dict[str, Any]]) -> str:
    width = 560
    row_height = 24
    start_y = 24
    max_rows = min(len(rows), 6)
    chart_height = start_y + max_rows * row_height + 16
    max_blockers = max((int(item.get("blockers", 0)) for item in rows[:max_rows]), default=1)
    max_blockers = max(max_blockers, 1)

    bars: list[str] = []
    for idx, item in enumerate(rows[:max_rows]):
        y = start_y + idx * row_height
        blockers = int(item.get("blockers", 0))
        w = int((blockers / max_blockers) * 280)
        label = str(item.get("project_id", "-"))
        bars.append(
            f"<text x='12' y='{y + 14}' font-size='11' fill='#5e6167'>{html.escape(label)}</text>"
            f"<rect x='170' y='{y + 2}' width='{w}' height='14' rx='5' fill='#ef4444' />"
            f"<text x='{170 + w + 8}' y='{y + 14}' font-size='11' fill='#1c1c1c'>{blockers} blockers</text>"
        )

    return (
        f"<svg viewBox='0 0 {width} {chart_height}' width='100%' height='{chart_height}' xmlns='http://www.w3.org/2000/svg'>"
        "<rect x='0' y='0' width='100%' height='100%' fill='#ffffff' rx='10'/>"
        + "".join(bars)
        + "</svg>"
    )


def _svg_issue_breakdown(issue: dict[str, Any]) -> str:
    total = max(int(issue.get("total", 0)), 1)
    todo = int(issue.get("todo", 0))
    in_progress = int(issue.get("in_progress", 0))
    blocked = int(issue.get("blocked", 0))
    done = int(issue.get("done", 0))

    w_todo = int((todo / total) * 500)
    w_prog = int((in_progress / total) * 500)
    w_block = int((blocked / total) * 500)
    w_done = 500 - w_todo - w_prog - w_block

    x_prog = 20 + w_todo
    x_block = x_prog + w_prog
    x_done = x_block + w_block

    return (
        "<svg viewBox='0 0 560 120' width='100%' height='120' xmlns='http://www.w3.org/2000/svg'>"
        "<rect x='0' y='0' width='100%' height='100%' fill='#ffffff' rx='10'/>"
        f"<rect x='20' y='34' width='{w_todo}' height='22' fill='#9ca3af' rx='6'/>"
        f"<rect x='{x_prog}' y='34' width='{w_prog}' height='22' fill='#2c5dff' rx='6'/>"
        f"<rect x='{x_block}' y='34' width='{w_block}' height='22' fill='#ef4444' rx='6'/>"
        f"<rect x='{x_done}' y='34' width='{max(w_done, 0)}' height='22' fill='#23a6a6' rx='6'/>"
        "<text x='20' y='78' font-size='11' fill='#5e6167'>todo</text>"
        f"<text x='58' y='78' font-size='11' fill='#1c1c1c'>{todo}</text>"
        "<text x='120' y='78' font-size='11' fill='#5e6167'>in_progress</text>"
        f"<text x='198' y='78' font-size='11' fill='#1c1c1c'>{in_progress}</text>"
        "<text x='272' y='78' font-size='11' fill='#5e6167'>blocked</text>"
        f"<text x='326' y='78' font-size='11' fill='#1c1c1c'>{blocked}</text>"
        "<text x='390' y='78' font-size='11' fill='#5e6167'>done</text>"
        f"<text x='426' y='78' font-size='11' fill='#1c1c1c'>{done}</text>"
        "</svg>"
    )


def _svg_agent_breakdown(agent: dict[str, int]) -> str:
    total = max(int(agent.get("total", 0)), 1)
    rest = int(agent.get("rest", 0))
    action = int(agent.get("action", 0))
    waiting = int(agent.get("waiting", 0))
    blocked = int(agent.get("blocked", 0))

    w_rest = int((rest / total) * 500)
    w_action = int((action / total) * 500)
    w_wait = int((waiting / total) * 500)
    w_block = 500 - w_rest - w_action - w_wait

    x_action = 20 + w_rest
    x_wait = x_action + w_action
    x_block = x_wait + w_wait

    return (
        "<svg viewBox='0 0 560 120' width='100%' height='120' xmlns='http://www.w3.org/2000/svg'>"
        "<rect x='0' y='0' width='100%' height='100%' fill='#ffffff' rx='10'/>"
        f"<rect x='20' y='34' width='{w_rest}' height='22' fill='#9ca3af' rx='6'/>"
        f"<rect x='{x_action}' y='34' width='{w_action}' height='22' fill='#2c5dff' rx='6'/>"
        f"<rect x='{x_wait}' y='34' width='{w_wait}' height='22' fill='#f59e0b' rx='6'/>"
        f"<rect x='{x_block}' y='34' width='{max(w_block, 0)}' height='22' fill='#ef4444' rx='6'/>"
        "<text x='20' y='78' font-size='11' fill='#5e6167'>repos</text>"
        f"<text x='58' y='78' font-size='11' fill='#1c1c1c'>{rest}</text>"
        "<text x='120' y='78' font-size='11' fill='#5e6167'>en action</text>"
        f"<text x='184' y='78' font-size='11' fill='#1c1c1c'>{action}</text>"
        "<text x='248' y='78' font-size='11' fill='#5e6167'>attente</text>"
        f"<text x='300' y='78' font-size='11' fill='#1c1c1c'>{waiting}</text>"
        "<text x='362' y='78' font-size='11' fill='#5e6167'>bloque</text>"
        f"<text x='406' y='78' font-size='11' fill='#1c1c1c'>{blocked}</text>"
        "</svg>"
    )


def _render_proof_links(project_dir: Path) -> str:
    candidates = [
        project_dir / "STATE.md",
        project_dir / "ROADMAP.md",
        project_dir / "DECISIONS.md",
    ]
    candidates.extend(sorted(project_dir.glob("CHECKPOINT*.md"))[:4])
    candidates.extend(sorted(project_dir.glob("PAPER_PLAN*.md"))[:4])

    rows: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        uri = _safe_uri(path)
        label = html.escape(path.name)
        if uri:
            rows.append(f"<li><a href='{html.escape(uri)}'>{label}</a></li>")
        else:
            rows.append(f"<li>{label}</li>")

    if not rows:
        return "<li>No proof files found.</li>"
    return "".join(rows)


def _base_style() -> str:
    return """
<style>
body {
  font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  background: #f6f3ee;
  color: #1c1c1c;
  margin: 0;
  padding: 12px;
}
h1 { margin: 0; font-size: 24px; color: #2c5dff; }
h2 { margin: 14px 0 8px 0; font-size: 16px; color: #2c5dff; }
h3 { margin: 8px 0 6px 0; font-size: 14px; color: #1c1c1c; }
p, li, td, th { font-size: 12px; line-height: 1.45; }
a { color: #2c5dff; text-decoration: none; }
a:hover { text-decoration: underline; }
.muted { color: #5e6167; }
.grid4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.card {
  background: #ffffff;
  border: 1px solid #d9d3c8;
  border-radius: 10px;
  padding: 10px;
}
.metric { font-size: 22px; font-weight: 700; color: #2c5dff; }
.badge {
  display: inline-block;
  border: 1px solid #d9d3c8;
  border-radius: 999px;
  padding: 3px 8px;
  margin-right: 6px;
  font-size: 11px;
  color: #5e6167;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border: 1px solid #d9d3c8;
  border-radius: 8px;
  overflow: hidden;
}
th, td {
  border-bottom: 1px solid #eee9df;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}
th { background: #f0ece6; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 980px) {
  .grid4, .grid2, .row { grid-template-columns: 1fr; }
}
</style>
"""



def _slo_verdict_card(project: ProjectData, pending: int, blockers_open: int) -> str:
    """Render SLO verdict card (GO / HOLD) based on settings targets."""
    settings = project.settings if isinstance(project.settings, dict) else {}
    slo = settings.get("slo") if isinstance(settings.get("slo"), dict) else {}
    targets = slo.get("targets") if isinstance(slo.get("targets"), dict) else {}

    p95 = targets.get("dispatch_p95_ms", 5000)
    p99 = targets.get("dispatch_p99_ms", 12000)
    success_min = targets.get("success_rate_min", 0.95)

    # Simple heuristic: GO if no blockers and queue is manageable
    verdict = "GO" if blockers_open == 0 and pending <= 3 else "HOLD"
    verdict_color = "#166534" if verdict == "GO" else "#92400E"
    verdict_bg = "#F0FDF4" if verdict == "GO" else "#FFFBEB"
    verdict_border = "#BBF7D0" if verdict == "GO" else "#FDE68A"
    verdict_icon = "&#x2705;" if verdict == "GO" else "&#x26A0;&#xFE0F;"

    return f"""<div class='card' style='background:{verdict_bg}; border: 1px solid {verdict_border};'>
      <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
        <div class='muted' style='font-size:11px;'>SLO Verdict</div>
        <span style='font-size:22px; font-weight:800; color:{verdict_color};'>{verdict_icon} {verdict}</span>
      </div>
      <table style='width:100%; font-size:11px; color:#5E6167;'>
        <tr><td>dispatch p95</td><td style='text-align:right; font-weight:600;'>&le; {p95} ms</td></tr>
        <tr><td>dispatch p99</td><td style='text-align:right; font-weight:600;'>&le; {p99} ms</td></tr>
        <tr><td>success rate</td><td style='text-align:right; font-weight:600;'>&ge; {int(success_min * 100)}%</td></tr>
        <tr><td>open blockers</td><td style='text-align:right; font-weight:600; color:{("#C94B4B" if blockers_open > 0 else "#166534")};'>{blockers_open}</td></tr>
        <tr><td>pending queue</td><td style='text-align:right; font-weight:600;'>{pending}</td></tr>
      </table>
    </div>"""


def _cost_panel_card(project: ProjectData) -> str:
    """Render CAD cost panel from project settings."""
    settings = project.settings if isinstance(project.settings, dict) else {}
    cost_cfg = settings.get("cost") if isinstance(settings.get("cost"), dict) else {}

    currency = cost_cfg.get("currency", "CAD")
    monthly_budget = cost_cfg.get("monthly_budget_cad", 0)

    if monthly_budget <= 0:
        return """<div class='card'>
          <div class='muted' style='font-size:11px;'>Co&ucirc;t mensuel</div>
          <div class='metric' style='color:#5E6167;'>n/a</div>
          <p class='muted'>Aucun budget configur&eacute;</p>
        </div>"""

    # Simple cost bar (no actual spend tracking yet — shows budget ceiling)
    bar_pct = min(100, 100)  # placeholder until telemetry wired
    bar_color = "#23A6A6" if bar_pct < 80 else ("#F59E0B" if bar_pct < 100 else "#C94B4B")

    return f"""<div class='card'>
      <div class='muted' style='font-size:11px;'>&#x1F4B0; Co&#xFB;t mensuel ({html.escape(currency)})</div>
      <div class='metric' style='font-size:20px;'>${monthly_budget:,.0f} <span style='font-size:12px; color:#5E6167;'>/ mois</span></div>
      <div style='background:#E8E2D9; border-radius:4px; height:8px; margin-top:8px;'>
        <div style='background:{bar_color}; width:{bar_pct}%; height:100%; border-radius:4px;'></div>
      </div>
      <p class='muted' style='margin-top:4px; font-size:10px;'>Budget plafond &mdash; t&eacute;l&eacute;m&eacute;trie non connect&eacute;e</p>
    </div>"""


def _build_project_html(project: ProjectData, mode: str, portfolio: list[ProjectData] | None) -> str:
    state = _state_bundle(project)
    issue = _issue_stats(project.path)
    agent = _agent_stats(project.agents)
    pending = _pending_requests(project.path)

    blockers_open = max(state["blockers_count"], int(agent["blocked"]))
    repo = _resolve_linked_repo_path(project.settings if isinstance(project.settings, dict) else {})

    repo_summary = ""
    if repo is not None and (repo / "README.md").exists():
        repo_summary = _extract_first_paragraph(repo / "README.md")
    if not repo_summary:
        repo_summary = _extract_first_paragraph(project.path / "README.md")
    if not repo_summary:
        repo_summary = "No repository summary available."

    gates = state["gates"][:5]
    next_items = state["next_top"][:5]
    now_items = state.get("now", [])
    now_text = now_items[0] if now_items else (state["objective"] or "n/a")

    if mode == "tech":
        mode_intro = (
            "Tech mode: contracts, gates, and verification first. "
            "Use this to confirm readiness before dispatch and release decisions."
        )
    else:
        mode_intro = (
            "Simple mode: quick operational reading in under 60 seconds. "
            "Focus on phase, blockers, next actions, and evidence paths."
        )

    # Now / Next / Blockers report card
    blockers_color = "#C94B4B" if blockers_open > 0 else "#166534"
    blockers_bg = "#FEF2F2" if blockers_open > 0 else "#F0FDF4"
    report_card = f"""
  <div class='card' style='background: #FFFBEB; border-left: 4px solid #F59E0B; margin-bottom: 12px;'>
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
      <h2 style='margin: 0; font-size: 15px;'>Rapport Now / Next / Blockers</h2>
      <span class='badge' style='font-size: 10px;'>Cadence: toutes les 2h | {html.escape(_utc_now_iso())}</span>
    </div>
    <div class='grid4' style='grid-template-columns: 1fr 1fr 1fr; gap: 8px;'>
      <div style='padding: 8px; background: #FFFFFF; border-radius: 8px; border: 1px solid #E5DED3;'>
        <div style='font-size: 11px; color: #5E6167; margin-bottom: 4px;'>&#x1F4CD; Now</div>
        <div style='font-size: 13px; font-weight: 600;'>{html.escape(now_text)}</div>
      </div>
      <div style='padding: 8px; background: #FFFFFF; border-radius: 8px; border: 1px solid #E5DED3;'>
        <div style='font-size: 11px; color: #5E6167; margin-bottom: 4px;'>&#x27A1;&#xFE0F; Next</div>
        <ul style='margin: 0; padding-left: 16px;'>{_render_list(next_items[:3], fallback='n/a')}</ul>
      </div>
      <div style='padding: 8px; background: {blockers_bg}; border-radius: 8px; border: 1px solid {blockers_color};'>
        <div style='font-size: 11px; color: {blockers_color}; margin-bottom: 4px;'>&#x1F6A7; Blockers ({blockers_open})</div>
        <ul style='margin: 0; padding-left: 16px;'>{_render_list(state['blockers'], fallback='Aucun')}</ul>
      </div>
    </div>
  </div>"""

    macro_block = ""
    if portfolio:
        snap = build_portfolio_snapshot(portfolio)
        rows = snap.get("rows", [])[:8]
        macro_rows = []
        for row in rows:
            pid = str(row.get("project_id", ""))
            link = f"pilotage://project/{pid}"
            macro_rows.append(
                "<tr>"
                f"<td><a href='{html.escape(link)}'>{html.escape(pid)}</a></td>"
                f"<td>{html.escape(str(row.get('phase', '-')))}</td>"
                f"<td>{int(row.get('done_pct', 0))}%</td>"
                f"<td>{int(row.get('blockers', 0))}</td>"
                f"<td>{int(row.get('active_agents', 0))}</td>"
                f"<td>{html.escape(str(row.get('dominant_risk', '-')))}</td>"
                "</tr>"
            )
        macro_block = (
            "<h2>Portfolio quick look</h2>"
            "<table><thead><tr>"
            "<th>Project</th><th>Phase</th><th>Done</th><th>Blockers</th><th>Active agents</th><th>Dominant risk</th>"
            "</tr></thead><tbody>"
            + "".join(macro_rows)
            + "</tbody></table>"
        )

    return f"""
<html><head>{_base_style()}</head><body>
  <h1>Pilotage - {html.escape(project.name)} ({html.escape(project.project_id)})</h1>
  <p class='muted'>Generated at {html.escape(_utc_now_iso())} | Scope: projet | Mode: {html.escape(mode)}</p>
  <p>{html.escape(mode_intro)}</p>

  {report_card}

  <div class='grid4'>
    <div class='card'><div class='muted'>Phase lifecycle</div><div class='metric'>{html.escape(state['phase'])}</div><p class='muted'>{state['phase_pct']}% of lifecycle</p></div>
    <div class='card'><div class='muted'>Issue progress</div><div class='metric'>{issue['done_pct']}%</div><p class='muted'>{issue['done']} done / {issue['total']} total</p></div>
    <div class='card'><div class='muted'>Open blockers</div><div class='metric'>{blockers_open}</div><p class='muted'>state + blocked agents</p></div>
    <div class='card'><div class='muted'>Pending requests</div><div class='metric'>{pending}</div><p class='muted'>queued/dispatched/reminded</p></div>
  </div>

  <div class='grid4' style='grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;'>
    {_slo_verdict_card(project, pending, blockers_open)}
    {_cost_panel_card(project)}
  </div>

  <h2>On est o\u00f9?</h2>
  <div class='card'>
    <div style='display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px;'>
      <span class='badge' style='background:#F0FDF4; color:#166534; border-color:#BBF7D0;'>&#x1F4A4; Repos {agent['rest']}</span>
      <span class='badge' style='background:#CEFBFB; color:#0F766E; border-color:#99F6E4;'>&#x26A1; En action {agent['action']}</span>
      <span class='badge' style='background:#DBEAFE; color:#1E40AF; border-color:#93C5FD;'>&#x23F3; Attente {agent['waiting']}</span>
      <span class='badge' style='background:#FEE2E2; color:#991B1B; border-color:#FECACA;'>&#x1F534; Bloqu\u00e9 {agent['blocked']}</span>
    </div>
    <h3>Issue status breakdown</h3>
    {_svg_issue_breakdown(issue)}
    <h3>Agent status breakdown</h3>
    {_svg_agent_breakdown(agent)}
  </div>

  <h2>On s\u2019en va o\u00f9?</h2>
  <div class='grid2'>
    <div class='card'>
      <h3>Next top 5</h3>
      <ul>{_render_list(next_items, fallback='No next items')}</ul>
    </div>
    <div class='card'>
      <h3>Milestones and gates imminents</h3>
      <ul>{_render_list(gates, fallback='No active gates')}</ul>
    </div>
  </div>

  <h2>Pourquoi?</h2>
  <div class='card'>
    <p><b>Objectif:</b> {html.escape(state['objective'] or 'n/a')}</p>
    <p><b>Contexte repo/projet:</b> {html.escape(repo_summary)}</p>
  </div>

  <h2>Comment?</h2>
  <div class='card'>
    <ul>
      <li>1. Intake and context lock</li>
      <li>2. Plan and ownership assignment</li>
      <li>3. Execution streams and quality gates</li>
      <li>4. Review and rollback checks</li>
      <li>5. Ship decision with evidence packet</li>
    </ul>
    <h3>Chemins de preuve</h3>
    <ul>{_render_proof_links(project.path)}</ul>
  </div>

  {macro_block}
</body></html>
"""


def _build_portfolio_html(project: ProjectData, mode: str, portfolio: list[ProjectData]) -> str:
    snap = build_portfolio_snapshot(portfolio)
    rows = snap.get("rows", [])
    top = snap.get("top_risks", [])

    table_rows: list[str] = []
    for row in rows:
        pid = str(row.get("project_id", ""))
        link = f"pilotage://project/{pid}"
        table_rows.append(
            "<tr>"
            f"<td><a href='{html.escape(link)}'>{html.escape(pid)}</a></td>"
            f"<td>{html.escape(str(row.get('phase', '-')))}</td>"
            f"<td>{int(row.get('done_pct', 0))}%</td>"
            f"<td>{int(row.get('blockers', 0))}</td>"
            f"<td>{int(row.get('active_agents', 0))}</td>"
            f"<td>{html.escape(str(row.get('dominant_risk', '-')))}</td>"
            "</tr>"
        )

    active_state = _state_bundle(project)
    active_issue = _issue_stats(project.path)
    active_agent = _agent_stats(project.agents)

    if mode == "tech":
        mode_intro = (
            "Tech mode: portfolio-level risk and delivery health. "
            "Use this view to pick escalation targets and stream rebalance decisions."
        )
    else:
        mode_intro = (
            "Simple mode: quick portfolio health. "
            "Identify where to intervene now and which project needs attention first."
        )

    return f"""
<html><head>{_base_style()}</head><body>
  <h1>Pilotage - Portfolio</h1>
  <p class='muted'>Generated at {html.escape(str(snap.get('generated_at', _utc_now_iso())))} | Scope: portefeuille | Mode: {html.escape(mode)}</p>
  <p>{html.escape(mode_intro)}</p>

  <div class='grid4'>
    <div class='card'><div class='muted'>Projects</div><div class='metric'>{int(snap.get('projects_count', 0))}</div></div>
    <div class='card'><div class='muted'>Total blockers</div><div class='metric'>{int(snap.get('total_blockers', 0))}</div></div>
    <div class='card'><div class='muted'>Active agents</div><div class='metric'>{int(snap.get('total_active_agents', 0))}</div></div>
    <div class='card'><div class='muted'>Focus project</div><div class='metric'>{html.escape(project.project_id)}</div></div>
  </div>

  <div class='row'>
    <div class='card'>
      <h2>Phase distribution</h2>
      {_svg_phase_distribution(snap.get('phase_distribution', {}))}
    </div>
    <div class='card'>
      <h2>Top projets a risque</h2>
      {_svg_top_risk(top)}
    </div>
  </div>

  <h2>Portfolio table</h2>
  <table>
    <thead>
      <tr>
        <th>Project</th>
        <th>Phase</th>
        <th>Done</th>
        <th>Blockers</th>
        <th>Active agents</th>
        <th>Dominant risk</th>
      </tr>
    </thead>
    <tbody>{''.join(table_rows) if table_rows else '<tr><td colspan="6" class="muted">No projects available.</td></tr>'}</tbody>
  </table>

  <h2>Focus projet actif - {html.escape(project.project_id)}</h2>
  <div class='grid4'>
    <div class='card'><div class='muted'>Phase</div><div class='metric'>{html.escape(active_state['phase'])}</div><p class='muted'>{active_state['phase_pct']}%</p></div>
    <div class='card'><div class='muted'>Issue done</div><div class='metric'>{active_issue['done_pct']}%</div><p class='muted'>{active_issue['done']} / {active_issue['total']}</p></div>
    <div class='card'><div class='muted'>Open blockers</div><div class='metric'>{max(active_state['blockers_count'], active_agent['blocked'])}</div></div>
    <div class='card'><div class='muted'>Pending requests</div><div class='metric'>{_pending_requests(project.path)}</div></div>
  </div>

  <div class='card'>
    <h2>Big picture + petit</h2>
    <ul>
      <li><b>Big picture:</b> compare phase mix, blocker pressure, and active agent load across projects.</li>
      <li><b>Petit:</b> click a project id in table to pivot into its micro view and action path.</li>
      <li><b>Why now:</b> keep decisions aligned with risk, not only with activity volume.</li>
    </ul>
  </div>
</body></html>
"""


def build_project_pilotage_html(
    project: ProjectData,
    *,
    mode: str = "simple",
    portfolio: list[ProjectData] | None = None,
    scope: str = "project",
) -> str:
    normalized_mode = str(mode or "simple").strip().lower()
    if normalized_mode not in {"simple", "tech"}:
        normalized_mode = "simple"

    normalized_scope = str(scope or "project").strip().lower()
    if normalized_scope not in {"project", "portfolio"}:
        normalized_scope = "project"

    try:
        if normalized_scope == "portfolio" and portfolio is not None:
            return _build_portfolio_html(project, normalized_mode, portfolio)
        return _build_project_html(project, normalized_mode, portfolio)
    except Exception as exc:  # noqa: BLE001
        return (
            "<html><body>"
            "<h1>Pilotage</h1>"
            "<p>Could not render pilotage dashboard.</p>"
            f"<p><code>{html.escape(str(exc))}</code></p>"
            "</body></html>"
        )
