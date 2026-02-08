#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import load_dispatch_counters
from app.services.auto_mode import compute_run_loop_kpi
from app.services.auto_mode import kpi_snapshots_path
from app.services.auto_mode import load_runtime_state
from app.services.auto_mode import resolve_projects_root


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _last_snapshot_age_seconds(path: Path, now: datetime) -> int | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for raw in reversed(lines):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        ts = _parse_iso(str(payload.get("timestamp") or ""))
        if ts is None:
            continue
        return max(int((now - ts).total_seconds()), 0)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Healthcheck for Cockpit auto-mode runtime state.")
    parser.add_argument("--project", default="demo", help="Project id")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Projects root. Special values: repo, app",
    )
    parser.add_argument("--stale-seconds", type=int, default=180, help="Max age for last tick")
    parser.add_argument("--max-open", type=int, default=50, help="Max open requests before degraded")
    args = parser.parse_args()

    projects_root = resolve_projects_root(args.data_dir)
    runtime = load_runtime_state(projects_root, args.project)
    counters = load_dispatch_counters(projects_root, args.project)
    kpi = compute_run_loop_kpi(projects_root, args.project, now=datetime.now(timezone.utc), window_hours=24, external_only=True)
    state_path = Path(str(runtime.get("state_path") or "")).expanduser()
    snapshot_path = kpi_snapshots_path(projects_root, args.project)

    now = datetime.now(timezone.utc)
    last_tick_at = _parse_iso(str(counters.get("last_tick_at") or ""))
    tick_age_seconds = None if last_tick_at is None else max(int((now - last_tick_at).total_seconds()), 0)
    snapshot_age_seconds = _last_snapshot_age_seconds(snapshot_path, now)

    open_requests = 0
    requests = runtime.get("requests", {})
    if isinstance(requests, dict):
        for payload in requests.values():
            if not isinstance(payload, dict):
                continue
            status = str(payload.get("status") or "").strip().lower()
            if status in {"queued", "dispatched", "reminded"}:
                open_requests += 1

    issues: list[str] = []
    if not state_path.exists():
        issues.append("missing_state_file")
    if last_tick_at is None:
        issues.append("missing_last_tick")
    elif tick_age_seconds is not None and tick_age_seconds > max(int(args.stale_seconds), 0):
        issues.append("stale_tick")
    if int(kpi.get("stale_queued_count") or 0) > 0:
        issues.append("stale_queued_count")
    if float(kpi.get("reminder_noise_pct") or 0.0) >= 5.0:
        issues.append("reminder_noise_high")
    dispatched_external_24h = int(kpi.get("dispatched_external_24h") or 0)
    close_rate_24h = float(kpi.get("close_rate_24h") or 0.0)
    if dispatched_external_24h > 0 and close_rate_24h < 90.0:
        issues.append("close_rate_low")
    if snapshot_age_seconds is None:
        issues.append("missing_kpi_snapshot")
    elif snapshot_age_seconds > 35 * 60:
        issues.append("stale_kpi_snapshot")
    if open_requests > max(int(args.max_open), 0):
        issues.append("too_many_open_requests")

    status = "healthy" if not issues else "degraded"
    payload = {
        "status": status,
        "project_id": args.project,
        "projects_root": str(projects_root),
        "state_path": str(state_path),
        "open_requests": open_requests,
        "tick_age_seconds": tick_age_seconds,
        "snapshot_age_seconds": snapshot_age_seconds,
        "kpi": kpi,
        "dispatch_latency_p95": kpi.get("dispatch_latency_p95"),
        "dispatch_latency_samples_24h": int(kpi.get("dispatch_latency_samples_24h") or 0),
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
