from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WINDOW_SPECS = {
    "24h": {"bucket_minutes": 60, "bucket_count": 24},
    "7d": {"bucket_minutes": 6 * 60, "bucket_count": 28},
    "30d": {"bucket_minutes": 24 * 60, "bucket_count": 30},
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse_iso(value: Any) -> datetime | None:
    token = str(value or "").strip()
    if not token:
        return None
    try:
        return datetime.fromisoformat(token.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
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


def _bucket_index(ts: datetime, starts: list[datetime], bucket_minutes: int) -> int | None:
    for index, start in enumerate(starts):
        end = start + timedelta(minutes=bucket_minutes)
        if start <= ts < end:
            return index
    return None


def build_pixel_feed(*, project_dir: Path, project_id: str, window: str) -> dict[str, Any]:
    spec = WINDOW_SPECS.get(str(window or "24h"), WINDOW_SPECS["24h"])
    bucket_minutes = int(spec["bucket_minutes"])
    bucket_count = int(spec["bucket_count"])
    now = _utc_now()
    starts = [now - timedelta(minutes=bucket_minutes * offset) for offset in reversed(range(bucket_count))]

    agent_ids: set[str] = set()
    agents_dir = project_dir / "agents"
    if agents_dir.exists():
        for entry in agents_dir.iterdir():
            if entry.is_dir():
                agent_ids.add(entry.name)

    rows: dict[str, list[dict[str, int]]] = {}

    def _ensure_agent(agent_id: str) -> list[dict[str, int]]:
        key = str(agent_id or "").strip() or "system"
        if key not in rows:
            rows[key] = [{"chat_messages": 0, "run_events": 0, "state_updates": 0} for _ in range(bucket_count)]
        agent_ids.add(key)
        return rows[key]

    for payload in _read_ndjson(project_dir / "chat" / "global.ndjson"):
        ts = _parse_iso(payload.get("timestamp"))
        if ts is None:
            continue
        idx = _bucket_index(ts, starts, bucket_minutes)
        if idx is None:
            continue
        author = str(payload.get("author") or "system")
        _ensure_agent(author)[idx]["chat_messages"] += 1

    runs_dir = project_dir / "runs"
    if runs_dir.exists():
        for path in runs_dir.glob("*.json"):
            payload = _read_json(path)
            if not payload:
                continue
            run_ts = _parse_iso(payload.get("generated_at") or payload.get("generated_at_utc"))
            if run_ts is None:
                try:
                    run_ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                except OSError:
                    run_ts = None
            if run_ts is None:
                continue
            idx = _bucket_index(run_ts, starts, bucket_minutes)
            if idx is None:
                continue
            messages = payload.get("messages")
            if isinstance(messages, list) and messages:
                for item in messages:
                    if not isinstance(item, dict):
                        continue
                    author = str(item.get("author") or "system")
                    _ensure_agent(author)[idx]["run_events"] += 1
            else:
                _ensure_agent("system")[idx]["run_events"] += 1

    for agent_id in list(agent_ids):
        state_path = project_dir / "agents" / agent_id / "state.json"
        if not state_path.exists():
            continue
        state_payload = _read_json(state_path)
        ts = _parse_iso(state_payload.get("updated_at") or state_payload.get("heartbeat"))
        if ts is None:
            continue
        idx = _bucket_index(ts, starts, bucket_minutes)
        if idx is None:
            continue
        _ensure_agent(agent_id)[idx]["state_updates"] += 1

    serialized_rows: list[dict[str, Any]] = []
    for agent_id in sorted(agent_ids):
        series = rows.get(agent_id) or [{"chat_messages": 0, "run_events": 0, "state_updates": 0} for _ in range(bucket_count)]
        cells: list[dict[str, Any]] = []
        for index, metrics in enumerate(series):
            total = int(metrics["chat_messages"]) + int(metrics["run_events"]) + int(metrics["state_updates"])
            intensity = 0 if total == 0 else min(3, total)
            cells.append(
                {
                    "bucket_start": starts[index].isoformat(),
                    "intensity": intensity,
                    "chat_messages": int(metrics["chat_messages"]),
                    "run_events": int(metrics["run_events"]),
                    "state_updates": int(metrics["state_updates"]),
                }
            )
        serialized_rows.append({"agent_id": agent_id, "cells": cells})

    return {
        "project_id": project_id,
        "window": "24h" if window not in WINDOW_SPECS else window,
        "bucket_minutes": bucket_minutes,
        "generated_at_utc": now.isoformat(),
        "rows": serialized_rows,
    }

