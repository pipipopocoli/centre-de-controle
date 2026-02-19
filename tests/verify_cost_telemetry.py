#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.cost_telemetry import (  # noqa: E402
    COST_EVENT_SCHEMA_VERSION,
    estimate_monthly_cad,
    estimate_monthly_cad_from_path,
    read_cost_events,
    validate_cost_event,
)


def _event(*, run_id: str, project_id: str, ts: float, timestamp: str, cost: float = 1.0, currency: str = "CAD") -> dict:
    return {
        "schema_version": COST_EVENT_SCHEMA_VERSION,
        "run_id": run_id,
        "project_id": project_id,
        "agent_id": "agent-11",
        "provider": "codex",
        "input_tokens": 10,
        "output_tokens": 20,
        "cached_tokens": 0,
        "cached_input_tokens": 0,
        "elapsed_ms": 12,
        "currency": currency,
        "cost_cad_estimate": cost,
        "timestamp": timestamp,
        "ts": ts,
    }


def main() -> int:
    now_utc = datetime(2026, 2, 19, 12, 0, 0, tzinfo=timezone.utc)
    previous_month = datetime(2026, 1, 31, 23, 0, 0, tzinfo=timezone.utc)

    valid = _event(
        run_id="run-1",
        project_id="cockpit",
        ts=now_utc.timestamp(),
        timestamp=now_utc.isoformat(),
        cost=2.5,
    )
    ok, reason = validate_cost_event(valid, project_id="cockpit")
    assert ok is True and reason is None

    bad_currency = dict(valid)
    bad_currency["currency"] = "USD"
    ok, reason = validate_cost_event(bad_currency, project_id="cockpit")
    assert ok is False and reason == "currency_not_cad"

    bad_negative = dict(valid)
    bad_negative["cost_cad_estimate"] = -1.0
    ok, reason = validate_cost_event(bad_negative, project_id="cockpit")
    assert ok is False and reason == "invalid_cost_cad_estimate_negative"

    bad_cached = dict(valid)
    bad_cached["cached_tokens"] = 2
    bad_cached["cached_input_tokens"] = 1
    ok, reason = validate_cost_event(bad_cached, project_id="cockpit")
    assert ok is False and reason == "cached_token_mismatch"

    events = [
        valid,
        _event(
            run_id="run-2",
            project_id="cockpit",
            ts=now_utc.timestamp() + 10,
            timestamp=now_utc.isoformat(),
            cost=3.25,
        ),
        _event(
            run_id="run-3",
            project_id="cockpit",
            ts=previous_month.timestamp(),
            timestamp=previous_month.isoformat(),
            cost=99.0,
        ),
        bad_currency,
        bad_negative,
    ]
    first_total, first_count = estimate_monthly_cad(events, now_utc=now_utc)
    second_total, second_count = estimate_monthly_cad(events, now_utc=now_utc)
    assert (first_total, first_count) == (second_total, second_count), "estimator must be deterministic"
    assert first_count == 2, f"expected 2 current-month valid events, got {first_count}"
    assert abs(first_total - 5.75) < 1e-9, f"unexpected monthly total: {first_total}"

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cost_events.ndjson"
        path.write_text(
            "\n".join(
                [
                    "{invalid-json",
                    json.dumps(valid),
                    json.dumps({"not": "a_cost_event"}),
                    json.dumps(events[1]),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        rows = read_cost_events(path)
        assert len(rows) == 3, "malformed JSON line must be skipped"
        monthly_total, monthly_count = estimate_monthly_cad_from_path(path, now_utc=now_utc)
        assert monthly_count == 2
        assert abs(monthly_total - 5.75) < 1e-9

    print("OK: cost telemetry schema + monthly estimator verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
