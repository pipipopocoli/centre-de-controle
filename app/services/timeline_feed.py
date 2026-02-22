from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.model import ProjectData

LANES = {"delivery", "runtime", "decision", "risk", "mission"}
SEVERITIES = {"info", "warn", "critical"}
SECTION_RE = re.compile(r"^##\s+(.+)$")
ISSUE_STATUS_RE = re.compile(r"^-+\s*Status:\s*(.+)$", re.IGNORECASE)
ISSUE_OWNER_RE = re.compile(r"^-+\s*Owner:\s*(.+)$", re.IGNORECASE)
ISSUE_PHASE_RE = re.compile(r"^-+\s*Phase:\s*(.+)$", re.IGNORECASE)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(payload, (dict, list)):
        return payload
    return None


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _to_iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return _to_iso(dt)


def _mtime_iso(path: Path) -> str:
    try:
        return _to_iso(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc))
    except Exception:
        return _to_iso(_utc_now())


def _safe_uri(path: Path) -> str:
    try:
        return path.resolve().as_uri()
    except Exception:
        return ""


def _norm_lane(value: str) -> str:
    lane = str(value or "").strip().lower()
    return lane if lane in LANES else "delivery"


def _norm_severity(value: str) -> str:
    sev = str(value or "").strip().lower()
    return sev if sev in SEVERITIES else "info"


def _event(
    *,
    event_id: str,
    ts_iso: str,
    lane: str,
    severity: str,
    title: str,
    details: str,
    source_path: str,
    source_uri: str,
) -> dict[str, str]:
    return {
        "event_id": event_id,
        "ts_iso": ts_iso,
        "lane": _norm_lane(lane),
        "severity": _norm_severity(severity),
        "title": title.strip() or "event",
        "details": details.strip(),
        "source_path": source_path,
        "source_uri": source_uri,
    }


def _parse_sections(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        section_match = SECTION_RE.match(line)
        if section_match:
            current = section_match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current and line.startswith("- "):
            value = line[2:].strip()
            if value:
                sections[current].append(value)
    return sections


def _primary_source_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for name, lane in (
        ("STATE.md", "delivery"),
        ("ROADMAP.md", "delivery"),
        ("DECISIONS.md", "decision"),
    ):
        path = project.path / name
        if not path.exists():
            continue
        title = name.replace(".md", "")
        events.append(
            _event(
                event_id=f"{project.project_id}:{title.lower()}",
                ts_iso=_mtime_iso(path),
                lane=lane,
                severity="info",
                title=f"{title} updated",
                details=f"{project.project_id} {title} changed",
                source_path=str(path),
                source_uri=_safe_uri(path),
            )
        )
    return events


def _issue_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    issues_dir = project.path / "issues"
    if not issues_dir.exists():
        return events

    for issue_path in sorted(issues_dir.glob("ISSUE-*.md")):
        title = issue_path.stem
        status = "todo"
        owner = "-"
        phase = "-"
        for raw in _read_text(issue_path).splitlines():
            line = raw.strip()
            if line.startswith("# ") and " - " in line:
                _, parsed_title = line[2:].split(" - ", 1)
                title = parsed_title.strip()
            status_match = ISSUE_STATUS_RE.match(line)
            if status_match:
                status = status_match.group(1).strip().lower()
            owner_match = ISSUE_OWNER_RE.match(line)
            if owner_match:
                owner = owner_match.group(1).strip()
            phase_match = ISSUE_PHASE_RE.match(line)
            if phase_match:
                phase = phase_match.group(1).strip()

        severity = "info"
        if status in {"blocked", "error", "failed", "timeout"}:
            severity = "critical"
        elif status in {"in progress", "in_progress", "wip", "active", "executing"}:
            severity = "warn"

        events.append(
            _event(
                event_id=f"{project.project_id}:{issue_path.stem}",
                ts_iso=_mtime_iso(issue_path),
                lane="delivery",
                severity=severity,
                title=f"{issue_path.stem} {status}",
                details=f"{title} | owner={owner} | phase={phase}",
                source_path=str(issue_path),
                source_uri=_safe_uri(issue_path),
            )
        )
    return events


def _runtime_request_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    path = project.path / "runs" / "requests.ndjson"
    if not path.exists():
        return events

    for idx, row in enumerate(_read_ndjson(path)):
        request_id = str(row.get("request_id") or f"request-{idx}").strip()
        agent_id = str(row.get("agent_id") or "-").strip()
        status = str(row.get("status") or "queued").strip().lower()
        ts_iso = (
            _parse_iso(row.get("updated_at"))
            or _parse_iso(row.get("closed_at"))
            or _parse_iso(row.get("dispatched_at"))
            or _parse_iso(row.get("created_at"))
            or _mtime_iso(path)
        )
        severity = "info"
        if status in {"failed", "error", "blocked", "timeout"}:
            severity = "critical"
        elif status in {"queued", "dispatched", "reminded"}:
            severity = "warn"
        title = f"request {request_id} {status}"
        details = f"agent={agent_id} source={str(row.get('source') or '-')}"
        events.append(
            _event(
                event_id=f"{project.project_id}:{request_id}:{idx}",
                ts_iso=ts_iso,
                lane="runtime",
                severity=severity,
                title=title,
                details=details,
                source_path=str(path),
                source_uri=_safe_uri(path),
            )
        )
    return events


def _kpi_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    path = project.path / "runs" / "kpi_snapshots.ndjson"
    if not path.exists():
        return events
    for idx, row in enumerate(_read_ndjson(path)):
        close_rate = row.get("close_rate_24h")
        stale = row.get("stale_queued_count")
        p95 = row.get("dispatch_latency_p95")
        ts_iso = _parse_iso(row.get("generated_at")) or _mtime_iso(path)
        severity = "info"
        try:
            if float(close_rate) < 80.0:
                severity = "critical"
            elif float(close_rate) < 95.0:
                severity = "warn"
        except (TypeError, ValueError):
            if int(stale or 0) > 0:
                severity = "warn"

        title = "kpi snapshot"
        details = f"close_rate_24h={close_rate} stale_queued={stale} p95={p95}"
        events.append(
            _event(
                event_id=f"{project.project_id}:kpi:{idx}",
                ts_iso=ts_iso,
                lane="runtime",
                severity=severity,
                title=title,
                details=details,
                source_path=str(path),
                source_uri=_safe_uri(path),
            )
        )
    return events


def _slo_event(project: ProjectData) -> list[dict[str, str]]:
    path = project.path / "runs" / "slo_verdict_latest.json"
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return []
    verdict = str(payload.get("verdict") or payload.get("status") or "unknown").strip().upper()
    severity = "info"
    if verdict == "HOLD":
        severity = "warn"
    elif verdict not in {"GO", "HOLD"}:
        severity = "critical"
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    details = (
        f"p95_ms={metrics.get('dispatch_p95_ms')} "
        f"p99_ms={metrics.get('dispatch_p99_ms')} "
        f"success_rate={metrics.get('success_rate')}"
    )
    ts_iso = _parse_iso(payload.get("generated_at")) or _parse_iso(payload.get("updated_at")) or _mtime_iso(path)
    return [
        _event(
            event_id=f"{project.project_id}:slo-verdict",
            ts_iso=ts_iso,
            lane="runtime",
            severity=severity,
            title=f"slo verdict {verdict}",
            details=details,
            source_path=str(path),
            source_uri=_safe_uri(path),
        )
    ]


def _mission_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    missions_dir = project.path / "missions"
    if missions_dir.exists():
        for mission_path in sorted(missions_dir.glob("*.md")):
            events.append(
                _event(
                    event_id=f"{project.project_id}:mission:{mission_path.stem}",
                    ts_iso=_mtime_iso(mission_path),
                    lane="mission",
                    severity="info",
                    title=f"mission {mission_path.stem}",
                    details="mission file updated",
                    source_path=str(mission_path),
                    source_uri=_safe_uri(mission_path),
                )
            )
    return events


def _checkpoint_events(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    paths = sorted(project.path.glob("CHECKPOINT*.md")) + sorted(project.path.glob("PAPER_PLAN*.md"))
    for path in paths:
        lane = "risk" if "RISK" in path.stem.upper() else "delivery"
        events.append(
            _event(
                event_id=f"{project.project_id}:doc:{path.stem}",
                ts_iso=_mtime_iso(path),
                lane=lane,
                severity="info",
                title=path.stem,
                details="checkpoint/paper updated",
                source_path=str(path),
                source_uri=_safe_uri(path),
            )
        )
    return events


def _risk_events_from_state(project: ProjectData) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    path = project.path / "STATE.md"
    if not path.exists():
        return events
    sections = _parse_sections(path)
    risks = sections.get("Risks") or []
    for idx, risk in enumerate(risks):
        if str(risk).strip().lower() in {"none", "n/a", "-"}:
            continue
        events.append(
            _event(
                event_id=f"{project.project_id}:risk:{idx}",
                ts_iso=_mtime_iso(path),
                lane="risk",
                severity="warn",
                title=f"risk {idx + 1}",
                details=str(risk),
                source_path=str(path),
                source_uri=_safe_uri(path),
            )
        )
    return events


def _milestones(project: ProjectData) -> list[dict[str, Any]]:
    state_path = project.path / "STATE.md"
    roadmap_path = project.path / "ROADMAP.md"
    state_sections = _parse_sections(state_path)
    roadmap_sections = _parse_sections(roadmap_path)

    phase = (state_sections.get("Phase") or ["Plan"])[0]
    objective = (state_sections.get("Objective") or [""])[0]
    blockers = [item for item in (state_sections.get("Blockers") or []) if item.strip().lower() not in {"none", "n/a", "-"}]
    next_items = (state_sections.get("Next") or roadmap_sections.get("Next") or [])[:5]
    gates = (
        (state_sections.get("Gates") or [])
        + (state_sections.get("Milestones") or [])
        + (state_sections.get("Checkpoints") or [])
    )[:6]

    return [
        {
            "project_id": project.project_id,
            "phase": phase,
            "objective": objective,
            "next": next_items,
            "blockers": blockers,
            "gates": gates,
        }
    ]


def _dedupe_events(events: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for event in events:
        key = (
            str(event.get("ts_iso") or ""),
            str(event.get("title") or ""),
            str(event.get("source_path") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(event)
    # Wave 6: Deterministic Sort Lock
    # 1. Primary key: (event_id, source_path, title)
    # 2. Secondary key: ts_iso (descending)
    out.sort(
        key=lambda item: (
            str(item.get("event_id") or ""),
            str(item.get("source_path") or ""),
            str(item.get("title") or ""),
        )
    )
    out.sort(key=lambda item: str(item.get("ts_iso") or ""), reverse=True)
    return out


def _stats(events: list[dict[str, str]]) -> dict[str, Any]:
    by_lane: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for event in events:
        lane = _norm_lane(str(event.get("lane") or "delivery"))
        severity = _norm_severity(str(event.get("severity") or "info"))
        source = str(event.get("source_path") or "-")
        by_lane[lane] = by_lane.get(lane, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_source[source] = by_source.get(source, 0) + 1
    return {
        "events_total": len(events),
        "by_lane": by_lane,
        "by_severity": by_severity,
        "sources_total": len(by_source),
    }


def _fallback_event(project: ProjectData) -> dict[str, str]:
    return _event(
        event_id=f"{project.project_id}:fallback",
        ts_iso=_to_iso(_utc_now()),
        lane="delivery",
        severity="info",
        title="no timeline events",
        details="No event source found yet.",
        source_path=str(project.path),
        source_uri=_safe_uri(project.path),
    )


def build_project_timeline_feed(project: ProjectData, limit: int = 120) -> dict[str, Any]:
    events: list[dict[str, str]] = []
    events.extend(_primary_source_events(project))
    events.extend(_issue_events(project))
    events.extend(_runtime_request_events(project))
    events.extend(_kpi_events(project))
    events.extend(_slo_event(project))
    events.extend(_mission_events(project))
    events.extend(_checkpoint_events(project))
    events.extend(_risk_events_from_state(project))

    deduped = _dedupe_events(events)
    if not deduped:
        deduped = [_fallback_event(project)]

    try:
        max_events = max(1, int(limit))
    except (TypeError, ValueError):
        max_events = 120
    trimmed = deduped[:max_events]

    return {
        "project_id": project.project_id,
        "generated_at": _to_iso(_utc_now()),
        "milestones": _milestones(project),
        "events": trimmed,
        "stats": _stats(trimmed),
    }


def build_portfolio_timeline_feed(projects: list[ProjectData], limit: int = 200) -> dict[str, Any]:
    canonical_projects = sorted(projects, key=lambda project: str(project.project_id or ""))
    events: list[dict[str, str]] = []
    milestones: list[dict[str, Any]] = []
    for project in canonical_projects:
        feed = build_project_timeline_feed(project, limit=max(20, int(limit / max(len(canonical_projects), 1))))
        milestones.extend(feed.get("milestones") if isinstance(feed.get("milestones"), list) else [])
        project_events = feed.get("events") if isinstance(feed.get("events"), list) else []
        for event in project_events:
            if not isinstance(event, dict):
                continue
            prefixed = dict(event)
            prefixed["event_id"] = f"{project.project_id}:{event.get('event_id')}"
            prefixed["title"] = f"[{project.project_id}] {str(event.get('title') or '')}".strip()
            events.append(prefixed)

    deduped = _dedupe_events(events)
    if not deduped and canonical_projects:
        deduped = [_fallback_event(canonical_projects[0])]
    try:
        max_events = max(1, int(limit))
    except (TypeError, ValueError):
        max_events = 200
    trimmed = deduped[:max_events]

    return {
        "generated_at": _to_iso(_utc_now()),
        "projects_count": len(canonical_projects),
        "milestones": milestones,
        "events": trimmed,
        "stats": _stats(trimmed),
    }
