from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import dispatch_once


def _write_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"

        reqs = [
            ("runreq_test_001", "agent-1", "msg_test_001", "Ping @agent-1 test"),
            ("runreq_test_002", "agent-2", "msg_test_002", "Ping @agent-2 test"),
            ("runreq_test_003", "agent-3", "msg_test_003", "Ping @agent-3 test"),
        ]
        for request_id, agent_id, msg_id, text in reqs:
            _write_ndjson(
                requests_path,
                {
                    "request_id": request_id,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "status": "queued",
                    "source": "mention",
                    "created_at": "2026-02-07T00:00:00Z",
                    "message": {
                        "message_id": msg_id,
                        "thread_id": None,
                        "author": "operator",
                        "text": text,
                        "tags": [],
                        "mentions": [agent_id],
                    },
                },
            )

        # Exact duplicate line for request_id must be dropped by queue recovery.
        _write_ndjson(
            requests_path,
            {
                "request_id": "runreq_test_001",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-07T00:00:01Z",
                "message": {
                    "message_id": "msg_test_001",
                    "thread_id": None,
                    "author": "operator",
                    "text": "Ping @agent-1 duplicate line",
                    "tags": [],
                    "mentions": ["agent-1"],
                },
            },
        )

        result_1 = dispatch_once(projects_root, project_id, max_actions=1)

        assert result_1.dispatched_count == 3, f"expected 3 dispatched, got {result_1.dispatched_count}"
        assert len(result_1.actions) == 1, f"expected max_actions=1, got {len(result_1.actions)}"
        assert result_1.actions[0].agent_id in {"agent-1", "agent-2", "agent-3"}, "unexpected action target"

        for _request_id, agent_id, _msg_id, _text in reqs:
            inbox = projects_root / project_id / "runs" / "inbox" / f"{agent_id}.ndjson"
            assert inbox.exists(), f"inbox not created for {agent_id}"
            inbox_lines = inbox.read_text(encoding="utf-8").splitlines()
            assert len(inbox_lines) == 1, f"expected 1 inbox line for {agent_id}, got {len(inbox_lines)}"

        state = projects_root / project_id / "runs" / "auto_mode_state.json"
        assert state.exists(), "state file not created"
        state_payload = json.loads(state.read_text(encoding="utf-8"))
        assert state_payload.get("schema_version") == 3, "runtime schema must be v3"

        processed = state_payload.get("processed")
        assert isinstance(processed, list), "processed list missing"
        requests_map = state_payload.get("requests")
        assert isinstance(requests_map, dict), "requests map missing"
        assert len(requests_map) >= len(processed), "requests map should cover processed ids"
        counters = state_payload.get("counters") if isinstance(state_payload.get("counters"), dict) else {}
        assert int(counters.get("queue_exact_dupe_removed_total") or 0) >= 1, "exact duplicate recovery counter missing"

        # Second run should not duplicate inbox entries and should produce no actions.
        result_2 = dispatch_once(projects_root, project_id, max_actions=1)
        assert result_2.dispatched_count == 0, f"expected 0 dispatched, got {result_2.dispatched_count}"
        assert len(result_2.actions) == 0, f"expected no actions, got {len(result_2.actions)}"
        for _request_id, agent_id, _msg_id, _text in reqs:
            inbox = projects_root / project_id / "runs" / "inbox" / f"{agent_id}.ndjson"
            inbox_lines = inbox.read_text(encoding="utf-8").splitlines()
            assert len(inbox_lines) == 1, f"expected dedupe for {agent_id}, got {len(inbox_lines)}"

    print("OK: auto-mode runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
