from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import (  # noqa: E402
    compute_run_loop_kpi,
    dispatch_once_with_counters,
    load_runtime_state,
    mark_agent_replied,
    mark_request_closed,
)


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _status_for(runtime: dict, request_id: str) -> str:
    requests = runtime.get("requests") or {}
    payload = requests.get(request_id) or {}
    return str(payload.get("status") or "")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"

        now = datetime.now(timezone.utc).replace(microsecond=0)
        request_id = "runreq_agent3_lifecycle_001"
        created_at = (now - timedelta(minutes=6)).isoformat()
        replied_at = (now - timedelta(minutes=2)).isoformat()
        closed_at = (now - timedelta(minutes=1)).isoformat()

        _append_ndjson(
            requests_path,
            {
                "request_id": request_id,
                "project_id": project_id,
                "agent_id": "agent-3",
                "status": "queued",
                "source": "mention",
                "created_at": created_at,
                "message": {
                    "message_id": "msg_agent3_lifecycle_001",
                    "thread_id": None,
                    "author": "victor",
                    "text": "@agent-3 Delegation: lifecycle test report",
                    "tags": ["delegation", "lifecycle", "test"],
                    "mentions": ["agent-3"],
                },
            },
        )

        transitions: list[str] = []
        runtime_0 = load_runtime_state(projects_root, project_id)
        transitions.append(_status_for(runtime_0, request_id) or "queued")

        dispatch_once_with_counters(projects_root, project_id, max_actions=1)
        runtime_1 = load_runtime_state(projects_root, project_id)
        status_1 = _status_for(runtime_1, request_id)
        assert status_1 == "dispatched", f"expected dispatched, got {status_1}"
        transitions.append(status_1)

        replied_request_id = mark_agent_replied(
            projects_root,
            project_id,
            "agent-3",
            reply_message_id="msg_agent3_reply_001",
            replied_at=replied_at,
        )
        assert replied_request_id == request_id, f"unexpected replied request id: {replied_request_id}"
        runtime_2 = load_runtime_state(projects_root, project_id)
        status_2 = _status_for(runtime_2, request_id)
        assert status_2 == "replied", f"expected replied, got {status_2}"
        transitions.append(status_2)

        closed = mark_request_closed(
            projects_root,
            project_id,
            request_id,
            closed_reason="reply_received",
            closed_at=closed_at,
        )
        assert closed.get("status") == "closed", f"expected closed, got {closed}"
        runtime_3 = load_runtime_state(projects_root, project_id)
        status_3 = _status_for(runtime_3, request_id)
        assert status_3 == "closed", f"expected closed, got {status_3}"
        transitions.append(status_3)

        expected = ["queued", "dispatched", "replied", "closed"]
        assert transitions == expected, f"unexpected lifecycle transitions: {transitions}"

        kpi = compute_run_loop_kpi(projects_root, project_id, now=now, external_only=True)
        assert kpi.get("dispatched_external_24h") == 1, f"unexpected kpi: {kpi}"
        assert kpi.get("closed_reply_received_24h") == 1, f"unexpected kpi: {kpi}"
        assert float(kpi.get("close_rate_24h") or 0.0) >= 90.0, f"close rate too low: {kpi}"

    print("OK: agent-3 lifecycle report verified")
    print("transitions: queued -> dispatched -> replied -> closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
