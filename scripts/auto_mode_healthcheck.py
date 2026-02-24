#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import (  # noqa: E402
    CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
    HEALTHCHECK_KPI_SNAPSHOT_MAX_AGE_SECONDS,
    emit_recency_autopulse_guard,
    recover_queue_state,
    resolve_projects_root,
)

OPEN_STATUSES = {"queued", "dispatched", "reminded"}
EXTERNAL_AGENTS = {"victor", "leo", "nova"}
ISSUE_DETAILS = {
    "missing_state_file": "auto_mode_state.json is missing for selected project root",
    "missing_last_activity": "no runtime activity timestamp found in state counters",
    "stale_tick": "latest runtime activity timestamp is older than stale-seconds threshold",
    "pulse_stale": "last_pulse_at is older than stale-seconds threshold",
    "too_many_open_requests": "open external requests exceed max-open threshold",
    "close_rate_low": "close-rate guard failed under active external pressure",
    "stale_kpi_snapshot": "latest KPI snapshot is older than max-snapshot-age-seconds",
}
WARNING_DETAILS = {
    "stale_kpi_snapshot_soft": (
        "kpi snapshot is stale but a recent pulse is present; snapshot recency is tracked as warning only"
    ),
}


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            out.append(payload)
    return out


def _is_external(agent_id: str) -> bool:
    raw = str(agent_id or "").strip().lower()
    if raw in EXTERNAL_AGENTS:
        return True
    if raw.startswith("agent-"):
        try:
            return int(raw.split("-", 1)[1]) % 2 == 1
        except (IndexError, ValueError):
            return True
    return False


def _compute_kpi(requests: list[dict[str, Any]], now: datetime, window_hours: int = 24) -> dict[str, Any]:
    cutoff = now - timedelta(hours=max(int(window_hours), 1))

    open_external = 0
    open_reminded = 0
    dispatched_external_24h = 0
    closed_reply_received_24h = 0

    for item in requests:
        agent_id = str(item.get("agent_id") or "")
        if not _is_external(agent_id):
            continue
        status = str(item.get("status") or "").strip().lower()
        if status in OPEN_STATUSES:
            open_external += 1
            if status == "reminded":
                open_reminded += 1

        dispatched_at = _parse_iso(str(item.get("dispatched_at") or "")) or _parse_iso(
            str(item.get("created_at") or "")
        )
        if dispatched_at and dispatched_at >= cutoff:
            dispatched_external_24h += 1

        closed_at = _parse_iso(str(item.get("closed_at") or ""))
        closed_reason = str(item.get("closed_reason") or "").strip().lower()
        if closed_reason == "reply_received" and closed_at and closed_at >= cutoff:
            closed_reply_received_24h += 1

    reminder_noise_pct = (open_reminded / max(open_external, 1)) * 100.0
    close_rate_24h = (closed_reply_received_24h / max(dispatched_external_24h, 1)) * 100.0

    return {
        "computed_at": now.replace(microsecond=0).isoformat(),
        "window_hours": int(window_hours),
        "open_external_total": open_external,
        "open_reminded_external": open_reminded,
        "dispatched_external_24h": dispatched_external_24h,
        "closed_reply_received_24h": closed_reply_received_24h,
        "reminder_noise_pct": round(reminder_noise_pct, 2),
        "close_rate_24h": round(close_rate_24h, 2),
    }


def _last_snapshot_age_seconds(path: Path, now: datetime) -> int | None:
    rows = _read_ndjson(path)
    for payload in reversed(rows):
        ts = _parse_iso(str(payload.get("timestamp") or "")) or _parse_iso(str(payload.get("generated_at") or ""))
        if ts:
            return max(int((now - ts).total_seconds()), 0)
    return None


def _latest_runtime_activity(state_payload: dict[str, Any]) -> datetime | None:
    counters = state_payload.get("counters")
    if not isinstance(counters, dict):
        counters = {}
    last_stats = counters.get("last_stats")
    if not isinstance(last_stats, dict):
        last_stats = {}

    candidates = [
        _parse_iso(str(counters.get("last_tick_at") or "")),
        _parse_iso(str(counters.get("last_pulse_at") or "")),
        _parse_iso(str(counters.get("dispatch_last_at") or "")),
        _parse_iso(str(last_stats.get("timestamp") or "")),
        _parse_iso(str(state_payload.get("updated_at") or "")),
    ]
    valid = [item for item in candidates if item is not None]
    if not valid:
        return None
    return max(valid)


def main() -> int:
    parser = argparse.ArgumentParser(description="Healthcheck for Cockpit auto-mode runtime state.")
    parser.add_argument("--project", default="cockpit", help="Project id")
    parser.add_argument("--data-dir", default=None, help="Projects root. Special values: repo, app")
    parser.add_argument("--stale-seconds", type=int, default=180, help="Max age for last tick")
    parser.add_argument("--max-open", type=int, default=50, help="Max open requests before degraded")
    parser.add_argument(
        "--max-snapshot-age-seconds",
        type=int,
        default=HEALTHCHECK_KPI_SNAPSHOT_MAX_AGE_SECONDS,
        help="Max age for latest KPI snapshot before degraded",
    )
    parser.add_argument(
        "--autopulse-guard",
        action="store_true",
        help=(
            "Try a recency-only KPI pulse refresh when snapshot is stale but pulse is fresh "
            "and no hard issues are present."
        ),
    )
    parser.add_argument(
        "--autopulse-min-interval-minutes",
        type=int,
        default=CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
        help="Minimum interval used by recency autopulse guard.",
    )
    parser.add_argument("--min-close-rate", type=float, default=80.0, help="Minimum close_rate_24h before degraded")
    parser.add_argument(
        "--min-dispatched-close-rate",
        type=int,
        default=5,
        help="Minimum dispatched_external_24h before enforcing close-rate threshold",
    )
    args = parser.parse_args()

    projects_root = resolve_projects_root(args.data_dir)
    project_dir = projects_root / args.project
    state_path = project_dir / "runs" / "auto_mode_state.json"
    snapshot_path = project_dir / "runs" / "kpi_snapshots.ndjson"

    now = datetime.now(timezone.utc)
    state_payload = _read_json(state_path)
    recovery = recover_queue_state(projects_root, args.project, persist=False, now=now)
    runtime_requests_map = recovery.get("runtime_requests")
    if not isinstance(runtime_requests_map, dict):
        runtime_requests_map = {}
    runtime_requests = [item for item in runtime_requests_map.values() if isinstance(item, dict)]
    lifecycle_mode = "runtime_v3" if runtime_requests else "legacy_v1"
    metric_requests = runtime_requests if runtime_requests else []
    kpi = _compute_kpi(metric_requests, now, window_hours=24)

    counters = state_payload.get("counters")
    if not isinstance(counters, dict):
        counters = {}

    last_tick_at = _parse_iso(str(counters.get("last_tick_at") or ""))
    last_pulse_at = _parse_iso(str(counters.get("last_pulse_at") or ""))
    last_activity_at = _latest_runtime_activity(state_payload)
    tick_age_seconds = None if last_activity_at is None else max(int((now - last_activity_at).total_seconds()), 0)
    snapshot_age_seconds = _last_snapshot_age_seconds(snapshot_path, now)

    open_requests_total = sum(
        1 for item in runtime_requests if str(item.get("status") or "").strip().lower() in OPEN_STATUSES
    )
    open_external_requests = sum(
        1
        for item in runtime_requests
        if str(item.get("status") or "").strip().lower() in OPEN_STATUSES
        and _is_external(str(item.get("agent_id") or ""))
    )
    open_external_inflight = sum(
        1
        for item in runtime_requests
        if str(item.get("status") or "").strip().lower() in {"dispatched", "reminded"}
        and _is_external(str(item.get("agent_id") or ""))
    )
    open_requests = int(open_external_requests)

    min_dispatched = max(int(args.min_dispatched_close_rate), 1)
    min_close_rate = float(args.min_close_rate)
    max_snapshot_age_seconds = max(int(args.max_snapshot_age_seconds), 0)

    issues: list[str] = []
    warnings: list[str] = []
    stale_seconds = max(int(args.stale_seconds), 0)
    pulse_age_seconds: int | None = None
    if not state_path.exists():
        issues.append("missing_state_file")
    if last_activity_at is None:
        issues.append("missing_last_activity")
    elif tick_age_seconds is not None and tick_age_seconds > stale_seconds:
        issues.append("stale_tick")
    if last_pulse_at is not None:
        pulse_age_seconds = max(int((now - last_pulse_at).total_seconds()), 0)
        if pulse_age_seconds > stale_seconds:
            issues.append("pulse_stale")
    max_open_threshold = max(int(args.max_open), 0)
    if open_requests > max_open_threshold:
        issues.append("too_many_open_requests")

    dispatched_external_24h = int(kpi.get("dispatched_external_24h") or 0)
    close_rate_24h = float(kpi.get("close_rate_24h") or 0.0)
    if (
        runtime_requests
        and open_external_requests > 0
        and open_external_inflight > 0
        and open_external_requests > max_open_threshold
        and dispatched_external_24h >= min_dispatched
        and close_rate_24h < min_close_rate
    ):
        issues.append("close_rate_low")

    snapshot_is_stale = bool(
        snapshot_path.exists()
        and snapshot_age_seconds is not None
        and snapshot_age_seconds > max_snapshot_age_seconds
    )
    pulse_is_fresh = pulse_age_seconds is not None and pulse_age_seconds <= stale_seconds
    if snapshot_is_stale:
        if pulse_is_fresh:
            warnings.append("stale_kpi_snapshot_soft")
        else:
            issues.append("stale_kpi_snapshot")

    hard_issues = [code for code in issues if code != "stale_kpi_snapshot"]
    autopulse_guard_result = emit_recency_autopulse_guard(
        projects_root,
        args.project,
        enabled=bool(args.autopulse_guard),
        stale_snapshot=snapshot_is_stale,
        pulse_fresh=pulse_is_fresh,
        hard_issues=hard_issues,
        now=now,
        min_interval_minutes=max(int(args.autopulse_min_interval_minutes), 1),
    )
    if bool(autopulse_guard_result.get("attempted")):
        snapshot_age_seconds = _last_snapshot_age_seconds(snapshot_path, now)
        snapshot_is_stale = bool(
            snapshot_path.exists()
            and snapshot_age_seconds is not None
            and snapshot_age_seconds > max_snapshot_age_seconds
        )
        issues = [code for code in issues if code != "stale_kpi_snapshot"]
        warnings = [code for code in warnings if code != "stale_kpi_snapshot_soft"]
        if snapshot_is_stale:
            if pulse_is_fresh:
                warnings.append("stale_kpi_snapshot_soft")
            else:
                issues.append("stale_kpi_snapshot")

    status = "healthy" if not issues else "degraded"

    payload = {
        "status": status,
        "project_id": args.project,
        "projects_root": str(projects_root),
        "mode": lifecycle_mode,
        "state_path": str(state_path),
        "open_requests": open_requests,
        "open_requests_external": int(open_external_requests),
        "open_external_inflight": int(open_external_inflight),
        "open_requests_total": int(open_requests_total),
        "requests_log_open_like": int(recovery.get("requests_log_open_like") or 0),
        "runtime_sync_closed_count": int(recovery.get("runtime_synced_closed") or 0),
        "runtime_missing_closed_count": int(recovery.get("runtime_missing_closed") or 0),
        "last_tick_at": last_tick_at.isoformat() if last_tick_at is not None else None,
        "last_pulse_at": last_pulse_at.isoformat() if last_pulse_at is not None else None,
        "pulse_age_seconds": pulse_age_seconds,
        "last_activity_at": last_activity_at.isoformat() if last_activity_at is not None else None,
        "tick_age_seconds": tick_age_seconds,
        "snapshot_age_seconds": snapshot_age_seconds,
        "max_snapshot_age_seconds": max_snapshot_age_seconds,
        "autopulse_guard_enabled": bool(args.autopulse_guard),
        "autopulse_guard_result": autopulse_guard_result,
        "kpi": kpi,
        "min_close_rate": min_close_rate,
        "min_dispatched_close_rate": min_dispatched,
        "kpi_snapshot_path": str(snapshot_path),
        "counters": counters,
        "issues": issues,
        "issue_details": {code: ISSUE_DETAILS.get(code, "unknown issue code") for code in issues},
        "warnings": warnings,
        "warning_details": {code: WARNING_DETAILS.get(code, "unknown warning code") for code in warnings},
    }

    print(json.dumps(payload, indent=2))
    print(
        f"auto_mode_healthcheck status={status} project={args.project} "
        f"open_requests={open_requests} tick_age_seconds={tick_age_seconds}"
    )
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
