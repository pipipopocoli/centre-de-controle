from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COST_EVENT_SCHEMA_VERSION = "wave05_cost_event_v2"

COST_EVENT_ERROR_EVENT_NOT_OBJECT = "event_not_object"
COST_EVENT_ERROR_SCHEMA_VERSION_MISMATCH = "schema_version_mismatch"
COST_EVENT_ERROR_PROJECT_ID_MISMATCH = "project_id_mismatch"
COST_EVENT_ERROR_MISSING_RUN_ID = "missing_run_id"
COST_EVENT_ERROR_MISSING_PROJECT_ID = "missing_project_id"
COST_EVENT_ERROR_MISSING_AGENT_ID = "missing_agent_id"
COST_EVENT_ERROR_MISSING_PROVIDER = "missing_provider"
COST_EVENT_ERROR_INVALID_INPUT_TOKENS_TYPE = "invalid_input_tokens_type"
COST_EVENT_ERROR_INVALID_INPUT_TOKENS_NEGATIVE = "invalid_input_tokens_negative"
COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_TYPE = "invalid_output_tokens_type"
COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_NEGATIVE = "invalid_output_tokens_negative"
COST_EVENT_ERROR_INVALID_CACHED_TOKENS_TYPE = "invalid_cached_tokens_type"
COST_EVENT_ERROR_INVALID_CACHED_TOKENS_NEGATIVE = "invalid_cached_tokens_negative"
COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_TYPE = "invalid_cached_input_tokens_type"
COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_NEGATIVE = "invalid_cached_input_tokens_negative"
COST_EVENT_ERROR_INVALID_ELAPSED_MS_TYPE = "invalid_elapsed_ms_type"
COST_EVENT_ERROR_INVALID_ELAPSED_MS_NEGATIVE = "invalid_elapsed_ms_negative"
COST_EVENT_ERROR_CACHED_TOKEN_MISMATCH = "cached_token_mismatch"
COST_EVENT_ERROR_CURRENCY_NOT_CAD = "currency_not_cad"
COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_TYPE = "invalid_cost_cad_estimate_type"
COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_NEGATIVE = "invalid_cost_cad_estimate_negative"
COST_EVENT_ERROR_INVALID_TS_TYPE = "invalid_ts_type"
COST_EVENT_ERROR_INVALID_TIMESTAMP = "invalid_timestamp"

COST_EVENT_ERROR_CODES = frozenset(
    {
        COST_EVENT_ERROR_EVENT_NOT_OBJECT,
        COST_EVENT_ERROR_SCHEMA_VERSION_MISMATCH,
        COST_EVENT_ERROR_PROJECT_ID_MISMATCH,
        COST_EVENT_ERROR_MISSING_RUN_ID,
        COST_EVENT_ERROR_MISSING_PROJECT_ID,
        COST_EVENT_ERROR_MISSING_AGENT_ID,
        COST_EVENT_ERROR_MISSING_PROVIDER,
        COST_EVENT_ERROR_INVALID_INPUT_TOKENS_TYPE,
        COST_EVENT_ERROR_INVALID_INPUT_TOKENS_NEGATIVE,
        COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_TYPE,
        COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_NEGATIVE,
        COST_EVENT_ERROR_INVALID_CACHED_TOKENS_TYPE,
        COST_EVENT_ERROR_INVALID_CACHED_TOKENS_NEGATIVE,
        COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_TYPE,
        COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_NEGATIVE,
        COST_EVENT_ERROR_INVALID_ELAPSED_MS_TYPE,
        COST_EVENT_ERROR_INVALID_ELAPSED_MS_NEGATIVE,
        COST_EVENT_ERROR_CACHED_TOKEN_MISMATCH,
        COST_EVENT_ERROR_CURRENCY_NOT_CAD,
        COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_TYPE,
        COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_NEGATIVE,
        COST_EVENT_ERROR_INVALID_TS_TYPE,
        COST_EVENT_ERROR_INVALID_TIMESTAMP,
    }
)


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
        return False, COST_EVENT_ERROR_EVENT_NOT_OBJECT

    schema_version = str(event.get("schema_version") or "").strip()
    if schema_version != COST_EVENT_SCHEMA_VERSION:
        return False, COST_EVENT_ERROR_SCHEMA_VERSION_MISMATCH

    if project_id is not None and str(event.get("project_id") or "").strip() != project_id:
        return False, COST_EVENT_ERROR_PROJECT_ID_MISMATCH

    required_str = ("run_id", "project_id", "agent_id", "provider")
    for key in required_str:
        if not str(event.get(key) or "").strip():
            if key == "run_id":
                return False, COST_EVENT_ERROR_MISSING_RUN_ID
            if key == "project_id":
                return False, COST_EVENT_ERROR_MISSING_PROJECT_ID
            if key == "agent_id":
                return False, COST_EVENT_ERROR_MISSING_AGENT_ID
            return False, COST_EVENT_ERROR_MISSING_PROVIDER

    for key in ("input_tokens", "output_tokens", "cached_tokens", "cached_input_tokens", "elapsed_ms"):
        value = event.get(key)
        if not isinstance(value, int):
            if key == "input_tokens":
                return False, COST_EVENT_ERROR_INVALID_INPUT_TOKENS_TYPE
            if key == "output_tokens":
                return False, COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_TYPE
            if key == "cached_tokens":
                return False, COST_EVENT_ERROR_INVALID_CACHED_TOKENS_TYPE
            if key == "cached_input_tokens":
                return False, COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_TYPE
            return False, COST_EVENT_ERROR_INVALID_ELAPSED_MS_TYPE
        if value < 0:
            if key == "input_tokens":
                return False, COST_EVENT_ERROR_INVALID_INPUT_TOKENS_NEGATIVE
            if key == "output_tokens":
                return False, COST_EVENT_ERROR_INVALID_OUTPUT_TOKENS_NEGATIVE
            if key == "cached_tokens":
                return False, COST_EVENT_ERROR_INVALID_CACHED_TOKENS_NEGATIVE
            if key == "cached_input_tokens":
                return False, COST_EVENT_ERROR_INVALID_CACHED_INPUT_TOKENS_NEGATIVE
            return False, COST_EVENT_ERROR_INVALID_ELAPSED_MS_NEGATIVE

    if int(event.get("cached_tokens")) != int(event.get("cached_input_tokens")):
        return False, COST_EVENT_ERROR_CACHED_TOKEN_MISMATCH

    currency = str(event.get("currency") or "").strip().upper()
    if currency != "CAD":
        return False, COST_EVENT_ERROR_CURRENCY_NOT_CAD

    cost_cad = event.get("cost_cad_estimate")
    if not _is_number(cost_cad):
        return False, COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_TYPE
    if float(cost_cad) < 0.0:
        return False, COST_EVENT_ERROR_INVALID_COST_CAD_ESTIMATE_NEGATIVE

    if not _is_number(event.get("ts")):
        return False, COST_EVENT_ERROR_INVALID_TS_TYPE
    if _event_datetime_utc(event) is None:
        return False, COST_EVENT_ERROR_INVALID_TIMESTAMP

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
