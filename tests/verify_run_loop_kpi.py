from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import (
    compute_run_loop_kpi,
    dispatch_once_with_counters,
    emit_kpi_snapshot,
    kpi_snapshots_path,
    mark_agent_replied,
    mark_request_closed,
)


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
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


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"
        now = datetime(2026, 2, 8, 7, 0, 0, tzinfo=timezone.utc)

        request_external = {
            "request_id": "runreq_kpi_ext_001",
            "project_id": project_id,
            "agent_id": "agent-1",
            "status": "queued",
            "source": "mention",
            "created_at": (now - timedelta(minutes=10)).replace(microsecond=0).isoformat(),
            "message": {
                "message_id": "msg_kpi_ext_001",
                "thread_id": None,
                "author": "operator",
                "text": "@agent-1 ping",
                "tags": [],
                "mentions": ["agent-1"],
            },
        }
        request_external_negative = {
            "request_id": "runreq_kpi_ext_neg_001",
            "project_id": project_id,
            "agent_id": "agent-3",
            "status": "queued",
            "source": "mention",
            "created_at": (datetime.now(timezone.utc) + timedelta(days=365)).replace(microsecond=0).isoformat(),
            "message": {
                "message_id": "msg_kpi_ext_neg_001",
                "thread_id": None,
                "author": "operator",
                "text": "@agent-3 ping",
                "tags": [],
                "mentions": ["agent-3"],
            },
        }
        request_internal = {
            "request_id": "runreq_kpi_int_001",
            "project_id": project_id,
            "agent_id": "clems",
            "status": "queued",
            "source": "mention",
            "created_at": (now - timedelta(minutes=10)).replace(microsecond=0).isoformat(),
            "message": {
                "message_id": "msg_kpi_int_001",
                "thread_id": None,
                "author": "operator",
                "text": "@clems update",
                "tags": [],
                "mentions": ["clems"],
            },
        }

        _append_ndjson(requests_path, request_external)
        _append_ndjson(requests_path, request_external_negative)
        _append_ndjson(requests_path, request_internal)

        dispatch_once_with_counters(projects_root, project_id, max_actions=0)

        replied_at = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat()
        request_id = mark_agent_replied(
            projects_root,
            project_id,
            "agent-1",
            reply_message_id="msg_reply_ext_001",
            replied_at=replied_at,
        )
        assert request_id == "runreq_kpi_ext_001", f"unexpected replied request: {request_id}"
        close = mark_request_closed(
            projects_root,
            project_id,
            request_id,
            closed_reason="reply_received",
            closed_at=replied_at,
        )
        assert close.get("status") == "closed", "external reply should close request"
        request_id_negative = mark_agent_replied(
            projects_root,
            project_id,
            "agent-3",
            reply_message_id="msg_reply_ext_neg_001",
            replied_at=replied_at,
        )
        assert request_id_negative == "runreq_kpi_ext_neg_001", f"unexpected replied request: {request_id_negative}"
        close_negative = mark_request_closed(
            projects_root,
            project_id,
            request_id_negative,
            closed_reason="reply_received",
            closed_at=replied_at,
        )
        assert close_negative.get("status") == "closed", "negative-latency request should still close"

        kpi = compute_run_loop_kpi(projects_root, project_id, now=now, external_only=True)
        assert kpi["dispatched_external_24h"] == 2, f"unexpected dispatched count: {kpi}"
        assert kpi["closed_reply_received_24h"] == 2, f"unexpected closed count: {kpi}"
        assert kpi["stale_queued_count"] == 0, f"unexpected stale count: {kpi}"
        assert kpi["reminder_noise_pct"] < 5.0, f"noise threshold failed: {kpi}"
        assert kpi["close_rate_24h"] >= 90.0, f"close rate threshold failed: {kpi}"
        assert "dispatch_latency_p95" in kpi, f"dispatch latency p95 missing: {kpi}"
        assert "dispatch_latency_samples_24h" in kpi, f"dispatch latency samples missing: {kpi}"
        assert "dispatch_latency_excluded_negative_24h" in kpi, f"dispatch latency exclusions missing: {kpi}"
        assert kpi["dispatch_latency_samples_24h"] >= 0, f"invalid dispatch latency samples: {kpi}"
        assert kpi["dispatch_latency_excluded_negative_24h"] >= 0, f"invalid dispatch latency exclusions: {kpi}"
        assert kpi["dispatch_latency_samples_24h"] == 1, f"unexpected dispatch latency sample size: {kpi}"
        assert kpi["dispatch_latency_excluded_negative_24h"] == 1, f"negative latency should be excluded: {kpi}"
        assert kpi["dispatch_latency_p95"] is None or kpi["dispatch_latency_p95"] >= 0, (
            f"invalid dispatch latency p95: {kpi}"
        )

        first = emit_kpi_snapshot(projects_root, project_id, now=now, post_chat=True, min_interval_minutes=25)
        assert first.get("emitted") is True, f"first snapshot should emit: {first}"

        second = emit_kpi_snapshot(
            projects_root,
            project_id,
            now=now + timedelta(minutes=5),
            post_chat=True,
            min_interval_minutes=25,
        )
        assert second.get("emitted") is False, f"second snapshot should be blocked by interval: {second}"
        assert second.get("reason") == "min_interval", f"unexpected skip reason: {second}"

        third = emit_kpi_snapshot(
            projects_root,
            project_id,
            now=now + timedelta(minutes=26),
            post_chat=True,
            min_interval_minutes=25,
        )
        assert third.get("emitted") is True, f"third snapshot should emit: {third}"

        snapshot_file = kpi_snapshots_path(projects_root, project_id)
        snapshots = _read_ndjson(snapshot_file)
        assert len(snapshots) == 2, f"expected exactly 2 persisted snapshots, got {len(snapshots)}"
        for snapshot in snapshots:
            assert "dispatch_latency_p95" in snapshot, f"snapshot missing p95: {snapshot}"
            assert "dispatch_latency_samples_24h" in snapshot, f"snapshot missing sample size: {snapshot}"
            assert "dispatch_latency_excluded_negative_24h" in snapshot, f"snapshot missing exclusions: {snapshot}"

        chat_file = projects_root / project_id / "chat" / "global.ndjson"
        chat_rows = _read_ndjson(chat_file)
        kpi_rows = [row for row in chat_rows if row.get("event") == "kpi_snapshot"]
        assert len(kpi_rows) == 2, f"expected 2 chat KPI snapshots, got {len(kpi_rows)}"
        for row in kpi_rows:
            text = str(row.get("text") or "")
            assert "dispatch_latency_p95=" in text, f"chat KPI snapshot missing dispatch latency line: {row}"

    print("OK: run-loop KPI snapshot + thresholds verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
