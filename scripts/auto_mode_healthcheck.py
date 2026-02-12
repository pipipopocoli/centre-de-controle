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

from app.services.auto_mode import resolve_projects_root  # noqa: E402

OPEN_STATUSES = {"queued", "dispatched", "reminded"}
EXTERNAL_AGENTS = {"victor", "leo"}


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


def _runtime_requests(state_payload: dict[str, Any]) -> list[dict[str, Any]]:
    reqs = state_payload.get("requests")
    if isinstance(reqs, dict):
        return [item for item in reqs.values() if isinstance(item, dict)]
    return []


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
        ts = _parse_iso(str(payload.get("timestamp") or ""))
        if ts:
            return max(int((now - ts).total_seconds()), 0)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Healthcheck for Cockpit auto-mode runtime state.")
    parser.add_argument("--project", default="cockpit", help="Project id")
    parser.add_argument("--data-dir", default=None, help="Projects root. Special values: repo, app")
    parser.add_argument("--stale-seconds", type=int, default=180, help="Max age for last tick")
    parser.add_argument("--max-open", type=int, default=50, help="Max open requests before degraded")
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
    requests_path = project_dir / "runs" / "requests.ndjson"
    snapshot_path = project_dir / "runs" / "kpi_snapshots.ndjson"

    now = datetime.now(timezone.utc)
    state_payload = _read_json(state_path)
    runtime_requests = _runtime_requests(state_payload)
    lifecycle_mode = "runtime_v3" if runtime_requests else "legacy_v1"
    metric_requests = runtime_requests if runtime_requests else []
    kpi = _compute_kpi(metric_requests, now, window_hours=24)

    counters = state_payload.get("counters")
    if not isinstance(counters, dict):
        counters = {}

    last_tick_at = _parse_iso(str(counters.get("last_tick_at") or state_payload.get("updated_at") or ""))
    tick_age_seconds = None if last_tick_at is None else max(int((now - last_tick_at).total_seconds()), 0)
    snapshot_age_seconds = _last_snapshot_age_seconds(snapshot_path, now)

    open_requests = sum(
        1 for item in runtime_requests if str(item.get("status") or "").strip().lower() in OPEN_STATUSES
    )

    min_dispatched = max(int(args.min_dispatched_close_rate), 1)
    min_close_rate = float(args.min_close_rate)

    issues: list[str] = []
    if not state_path.exists():
        issues.append("missing_state_file")
    if last_tick_at is None:
        issues.append("missing_last_tick")
    elif tick_age_seconds is not None and tick_age_seconds > max(int(args.stale_seconds), 0):
        issues.append("stale_tick")
    if open_requests > max(int(args.max_open), 0):
        issues.append("too_many_open_requests")

    dispatched_external_24h = int(kpi.get("dispatched_external_24h") or 0)
    close_rate_24h = float(kpi.get("close_rate_24h") or 0.0)
    if runtime_requests and dispatched_external_24h >= min_dispatched and close_rate_24h < min_close_rate:
        issues.append("close_rate_low")

    if snapshot_path.exists() and snapshot_age_seconds is not None and snapshot_age_seconds > 35 * 60:
        issues.append("stale_kpi_snapshot")

    status = "healthy" if not issues else "degraded"

    payload = {
        "status": status,
        "project_id": args.project,
        "projects_root": str(projects_root),
        "mode": lifecycle_mode,
        "state_path": str(state_path),
        "open_requests": open_requests,
        "tick_age_seconds": tick_age_seconds,
        "snapshot_age_seconds": snapshot_age_seconds,
        "kpi": kpi,
        "min_close_rate": min_close_rate,
        "min_dispatched_close_rate": min_dispatched,
        "kpi_snapshot_path": str(snapshot_path),
        "counters": counters,
        "issues": issues,
    }

    print(json.dumps(payload, indent=2))
    print(
        f"auto_mode_healthcheck status={status} project={args.project} "
        f"open_requests={open_requests} tick_age_seconds={tick_age_seconds}"
    )
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
