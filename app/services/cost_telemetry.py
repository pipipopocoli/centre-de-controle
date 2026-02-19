from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COST_EVENT_SCHEMA_VERSION = "wave05_cost_event_v2"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_iso_utc(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_datetime_utc(event: dict[str, Any]) -> datetime | None:
    ts_raw = event.get("ts")
    if _is_number(ts_raw):
        try:
            return datetime.fromtimestamp(float(ts_raw), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None
    return _parse_iso_utc(event.get("timestamp"))


def validate_cost_event(event: dict[str, Any], project_id: str | None = None) -> tuple[bool, str | None]:
    if not isinstance(event, dict):
        return False, "event_not_object"

    schema_version = str(event.get("schema_version") or "").strip()
    if schema_version != COST_EVENT_SCHEMA_VERSION:
        return False, "schema_version_mismatch"

    if project_id is not None and str(event.get("project_id") or "").strip() != project_id:
        return False, "project_id_mismatch"

    required_str = ("run_id", "project_id", "agent_id", "provider")
    for key in required_str:
        if not str(event.get(key) or "").strip():
            return False, f"missing_{key}"

    for key in ("input_tokens", "output_tokens", "cached_tokens", "cached_input_tokens", "elapsed_ms"):
        value = event.get(key)
        if not isinstance(value, int):
            return False, f"invalid_{key}_type"
        if value < 0:
            return False, f"invalid_{key}_negative"

    if int(event.get("cached_tokens")) != int(event.get("cached_input_tokens")):
        return False, "cached_token_mismatch"

    currency = str(event.get("currency") or "").strip().upper()
    if currency != "CAD":
        return False, "currency_not_cad"

    cost_cad = event.get("cost_cad_estimate")
    if not _is_number(cost_cad):
        return False, "invalid_cost_cad_estimate_type"
    if float(cost_cad) < 0.0:
        return False, "invalid_cost_cad_estimate_negative"

    if not _is_number(event.get("ts")):
        return False, "invalid_ts_type"
    if _event_datetime_utc(event) is None:
        return False, "invalid_timestamp"

    return True, None


def read_cost_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
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


def estimate_monthly_cad(events: list[dict[str, Any]], now_utc: datetime) -> tuple[float, int]:
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)
    month_key = now_utc.strftime("%Y-%m")

    monthly_total = 0.0
    event_count = 0
    for event in events:
        is_valid, _ = validate_cost_event(event)
        if not is_valid:
            continue
        dt = _event_datetime_utc(event)
        if dt is None or dt.strftime("%Y-%m") != month_key:
            continue
        monthly_total += float(event.get("cost_cad_estimate", 0.0))
        event_count += 1

    return round(monthly_total, 6), event_count


def estimate_monthly_cad_from_path(path: Path, now_utc: datetime) -> tuple[float, int]:
    return estimate_monthly_cad(read_cost_events(path), now_utc)


def legacy_monthly_cad_estimate(payload: dict[str, Any] | None) -> float | None:
    if not isinstance(payload, dict):
        return None
    value_cad = payload.get("api_cost_cad")
    if _is_number(value_cad):
        return float(value_cad)
    value_usd = payload.get("api_cost_usd")
    if _is_number(value_usd):
        return float(value_usd) * 1.35
    return None
