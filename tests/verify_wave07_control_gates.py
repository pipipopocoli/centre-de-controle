#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import compute_control_gate_snapshot  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        runs_dir = project_dir / "runs"
        agents_dir = project_dir / "agents"

        now = datetime(2026, 2, 19, 18, 0, 0, tzinfo=timezone.utc)
        now_iso = now.replace(microsecond=0).isoformat()

        # Noisy append-only requests log: 4 open-like rows.
        requests_path = runs_dir / "requests.ndjson"
        for idx in range(4):
            _append_ndjson(
                requests_path,
                {
                    "request_id": f"log_open_{idx}",
                    "project_id": project_id,
                    "agent_id": f"agent-{idx+1}",
                    "status": "queued",
                    "created_at": now_iso,
                },
            )

        # Runtime state is authoritative and clean: all requests already closed.
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": ["req_closed_1", "req_closed_2"],
                "requests": {
                    "req_closed_1": {
                        "request_id": "req_closed_1",
                        "project_id": project_id,
                        "agent_id": "agent-1",
                        "status": "closed",
                        "created_at": now_iso,
                        "closed_at": now_iso,
                    },
                    "req_closed_2": {
                        "request_id": "req_closed_2",
                        "project_id": project_id,
                        "agent_id": "agent-2",
                        "status": "closed",
                        "created_at": now_iso,
                        "closed_at": now_iso,
                    },
                },
                "counters": {},
                "updated_at": now_iso,
            },
        )

        # Heartbeat metric remains independent from queue metric.
        stale_hb = (now - timedelta(hours=2)).replace(microsecond=0).isoformat()
        fresh_hb = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat()
        _write_json(
            agents_dir / "agent-1" / "state.json",
            {"agent_id": "agent-1", "status": "idle", "heartbeat": stale_hb},
        )
        _write_json(
            agents_dir / "agent-2" / "state.json",
            {"agent_id": "agent-2", "status": "idle", "heartbeat": fresh_hb},
        )

        snapshot_clean = compute_control_gate_snapshot(projects_root, project_id, now=now)
        assert snapshot_clean["queued_runtime_requests"] == 0, "queue metric must come from runtime state"
        assert snapshot_clean["pending_stale_gt24h"] == 0
        assert snapshot_clean["queued_runtime_requests_ok"] is True
        assert snapshot_clean["pending_stale_gt24h_ok"] is True
        assert snapshot_clean["stale_heartbeats_gt1h"] == 1
        assert isinstance(snapshot_clean["stale_heartbeats_gt1h_ok"], bool)
        assert snapshot_clean["sources"]["requests_log_open_like"] == 4, "audit source should expose ndjson drift"
        assert snapshot_clean["sources"]["runtime_sync_closed_count"] == 0
        assert snapshot_clean["sources"]["duplicate_groups_closed_count"] == 0

        # Runtime queued + latest log closed for same request: runtime must be synced closed in snapshot view.
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_sync_close",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "closed",
                "created_at": now_iso,
                "closed_at": now_iso,
                "closed_reason": "queue_hygiene_runtime_recovery",
            },
        )
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_sync_close": {
                        "request_id": "req_sync_close",
                        "project_id": project_id,
                        "agent_id": "agent-1",
                        "status": "queued",
                        "created_at": now_iso,
                    }
                },
                "counters": {},
                "updated_at": now_iso,
            },
        )
        snapshot_synced = compute_control_gate_snapshot(projects_root, project_id, now=now)
        assert snapshot_synced["queued_runtime_requests"] == 0
        assert snapshot_synced["sources"]["runtime_sync_closed_count"] == 1

        # Runtime now has one stale queued request: gate must reflect runtime map.
        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_open_stale": {
                        "request_id": "req_open_stale",
                        "project_id": project_id,
                        "agent_id": "agent-1",
                        "status": "queued",
                        "created_at": (now - timedelta(hours=25)).replace(microsecond=0).isoformat(),
                    }
                },
                "counters": {},
                "updated_at": now_iso,
            },
        )
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_open_stale",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "created_at": (now - timedelta(hours=25)).replace(microsecond=0).isoformat(),
            },
        )

        snapshot_stale = compute_control_gate_snapshot(projects_root, project_id, now=now)
        assert snapshot_stale["queued_runtime_requests"] == 1
        assert snapshot_stale["pending_stale_gt24h"] == 1
        assert snapshot_stale["queued_runtime_requests_ok"] is True
        assert snapshot_stale["pending_stale_gt24h_ok"] is False
        assert snapshot_stale["stale_heartbeats_gt1h"] == 1

    print("OK: wave07 control gate snapshot verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
