#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import compute_control_gate_snapshot, load_runtime_state, recover_queue_state  # noqa: E402


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_ndjson(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        runs_dir = projects_root / project_id / "runs"
        requests_path = runs_dir / "requests.ndjson"
        now = datetime(2026, 2, 20, 20, 30, 0, tzinfo=timezone.utc)
        now_iso = now.replace(microsecond=0).isoformat()

        # Exact duplicate line (same request_id) -> keep only latest line.
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_exact_dup",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-20T20:00:00+00:00",
                "message": {"message_id": "msg_exact", "author": "operator", "text": "Ping @agent-1", "mentions": ["agent-1"]},
            },
        )
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_exact_dup",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-20T20:01:00+00:00",
                "message": {"message_id": "msg_exact", "author": "operator", "text": "Ping @agent-1 duplicate", "mentions": ["agent-1"]},
            },
        )

        # Semantic duplicates (same message_id + agent_id, different request_ids).
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_sem_old",
                "project_id": project_id,
                "agent_id": "agent-2",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-20T20:02:00+00:00",
                "message": {"message_id": "msg_sem", "author": "operator", "text": "Ping @agent-2 old", "mentions": ["agent-2"]},
            },
        )
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_sem_new",
                "project_id": project_id,
                "agent_id": "agent-2",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-20T20:03:00+00:00",
                "message": {"message_id": "msg_sem", "author": "operator", "text": "Ping @agent-2 new", "mentions": ["agent-2"]},
            },
        )

        # Runtime/log reconciliation fixture: runtime open but latest log closed.
        _append_ndjson(
            requests_path,
            {
                "request_id": "req_sync",
                "project_id": project_id,
                "agent_id": "agent-3",
                "status": "closed",
                "source": "mention",
                "created_at": "2026-02-20T20:04:00+00:00",
                "closed_at": "2026-02-20T20:10:00+00:00",
                "closed_reason": "runner_completed",
                "message": {"message_id": "msg_sync", "author": "operator", "text": "Ping @agent-3", "mentions": ["agent-3"]},
            },
        )

        _write_json(
            runs_dir / "auto_mode_state.json",
            {
                "schema_version": 3,
                "processed": [],
                "requests": {
                    "req_sync": {
                        "request_id": "req_sync",
                        "project_id": project_id,
                        "agent_id": "agent-3",
                        "status": "queued",
                        "created_at": "2026-02-20T20:04:00+00:00",
                    }
                },
                "counters": {},
                "updated_at": now_iso,
            },
        )

        recovery = recover_queue_state(projects_root, project_id, persist=True, now=now)
        assert recovery["exact_dupes_removed"] == 1, f"expected 1 exact duplicate removal: {recovery}"
        assert recovery["semantic_dupes_closed"] == 1, f"expected 1 semantic duplicate closure: {recovery}"
        assert recovery["duplicate_groups_closed"] == 1, f"expected 1 duplicate group closure: {recovery}"
        assert recovery["runtime_synced_closed"] == 1, f"expected runtime sync closure: {recovery}"

        rows = _read_ndjson(requests_path)
        id_counts = Counter(str(row.get("request_id") or "") for row in rows)
        dup_ids = {rid: count for rid, count in id_counts.items() if rid and count > 1}
        assert not dup_ids, f"duplicate request_id rows remain: {dup_ids}"

        by_id = {str(row.get("request_id") or ""): row for row in rows}
        assert by_id["req_sem_old"]["status"] == "closed", f"old semantic duplicate must be closed: {by_id['req_sem_old']}"
        assert by_id["req_sem_old"]["closed_reason"] == "duplicate_recovery"
        assert by_id["req_sem_new"]["status"] == "queued", f"latest semantic duplicate must stay queued: {by_id['req_sem_new']}"

        runtime = load_runtime_state(projects_root, project_id)
        req_sync = runtime["requests"]["req_sync"]
        assert req_sync["status"] == "closed", f"runtime req_sync should be closed: {req_sync}"
        assert req_sync["closed_reason"] == "runner_completed", f"runtime req_sync reason mismatch: {req_sync}"

        counters = runtime.get("counters", {})
        assert int(counters.get("queue_exact_dupe_removed_total") or 0) >= 1
        assert int(counters.get("queue_semantic_dupe_closed_total") or 0) >= 1
        assert int(counters.get("runtime_log_sync_closed_total") or 0) >= 1

        snapshot = compute_control_gate_snapshot(projects_root, project_id, now=now)
        assert snapshot["queued_runtime_requests"] <= 3, f"queue target drift: {snapshot}"
        assert snapshot["queued_runtime_requests_ok"] is True

    print("OK: wave07 queue recovery verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
