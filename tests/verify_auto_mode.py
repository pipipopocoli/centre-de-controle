from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import (
    dispatch_once,
    iter_reminder_candidates,
    load_runtime_state,
    mark_agent_replied,
    mark_request_reminded,
)


def _write_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        requests_path = projects_root / project_id / "runs" / "requests.ndjson"
        now = datetime.now(timezone.utc)

        reqs = [
            (
                "runreq_test_001",
                "agent-1",
                "msg_test_001",
                "[Cockpit auto-mode]\nProject: demo\nTask:\nPing @agent-1 test\nInstructions:\n- old",
            ),
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
                    "created_at": (now - timedelta(minutes=10)).replace(microsecond=0).isoformat(),
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

        # Reminder-source requests should never be dispatched by auto-mode.
        _write_ndjson(
            requests_path,
            {
                "request_id": "runreq_test_internal_clems",
                "project_id": project_id,
                "agent_id": "clems",
                "status": "queued",
                "source": "mention",
                "created_at": now.replace(microsecond=0).isoformat(),
                "message": {
                    "message_id": "msg_internal_clems",
                    "thread_id": None,
                    "author": "operator",
                    "text": "@clems ping",
                    "tags": [],
                    "mentions": ["clems"],
                },
            },
        )

        _write_ndjson(
            requests_path,
            {
                "request_id": "runreq_test_reminder",
                "project_id": project_id,
                "agent_id": "agent-4",
                "status": "queued",
                "source": "reminder",
                "created_at": now.replace(microsecond=0).isoformat(),
                "message": {
                    "message_id": "msg_reminder",
                    "thread_id": None,
                    "author": "clems",
                    "text": "Rappel @agent-4",
                    "tags": [],
                    "mentions": ["agent-4"],
                },
            },
        )

        result_1 = dispatch_once(projects_root, project_id, max_actions=1)

        assert result_1.dispatched_count == 3, f"expected 3 dispatched, got {result_1.dispatched_count}"
        assert len(result_1.actions) == 1, f"expected max_actions=1, got {len(result_1.actions)}"
        assert result_1.actions[0].agent_id == "agent-1", "expected first action to be agent-1"
        assert result_1.skipped_reminder == 1, f"expected 1 reminder skip, got {result_1.skipped_reminder}"
        assert result_1.skipped_internal_agent == 1, "internal agents must be skipped from external dispatch"
        assert result_1.skipped_old == 0, f"expected no old skip, got {result_1.skipped_old}"
        assert (
            "PROJECT LOCK: cockpit" in result_1.actions[0].prompt_text
        ), "prompt must include explicit project lock"
        assert (
            "Task:\\nPing @agent-1 test" in result_1.actions[0].prompt_text
        ), "nested auto-mode envelopes must be flattened to latest task body"
        assert (
            "PROJECT LOCK: cockpit" not in result_1.actions[0].prompt_text.split("Task:\\n", 1)[-1]
        ), "nested auto-mode envelopes must be sanitized in task body"

        for _request_id, agent_id, _msg_id, _text in reqs:
            inbox = projects_root / project_id / "runs" / "inbox" / f"{agent_id}.ndjson"
            assert inbox.exists(), f"inbox not created for {agent_id}"
            inbox_lines = inbox.read_text(encoding="utf-8").splitlines()
            assert len(inbox_lines) == 1, f"expected 1 inbox line for {agent_id}, got {len(inbox_lines)}"

        state = projects_root / project_id / "runs" / "auto_mode_state.json"
        assert state.exists(), "state file not created"
        runtime = load_runtime_state(projects_root, project_id)
        assert "processed" in runtime and "requests" in runtime, "runtime state missing required fields"
        assert len(runtime["processed"]) == 5, "processed ids should include dispatched + skipped closure events"
        for request_id, payload in runtime["requests"].items():
            if request_id not in {"runreq_test_001", "runreq_test_002", "runreq_test_003"}:
                continue
            assert payload.get("status") == "dispatched", "newly dispatched requests must be marked dispatched"
            assert int(payload.get("reminder_count") or 0) == 0, "initial reminder_count should be 0"
        clems_request = runtime["requests"]["runreq_test_internal_clems"]
        assert clems_request.get("status") == "closed", "internal clems request must close immediately"
        assert clems_request.get("closed_reason") == "internal_agent_not_dispatchable"

        # Second run should not duplicate inbox entries and should produce no actions.
        result_2 = dispatch_once(projects_root, project_id, max_actions=1)
        assert result_2.dispatched_count == 0, f"expected 0 dispatched, got {result_2.dispatched_count}"
        assert len(result_2.actions) == 0, f"expected no actions, got {len(result_2.actions)}"
        for _request_id, agent_id, _msg_id, _text in reqs:
            inbox = projects_root / project_id / "runs" / "inbox" / f"{agent_id}.ndjson"
            inbox_lines = inbox.read_text(encoding="utf-8").splitlines()
            assert len(inbox_lines) == 1, f"expected dedupe for {agent_id}, got {len(inbox_lines)}"

        # Mark agent reply and ensure lifecycle status advances.
        replied_request = mark_agent_replied(
            projects_root,
            project_id,
            "agent-2",
            reply_message_id="msg_reply_agent2",
            replied_at=(now + timedelta(minutes=12)).replace(microsecond=0).isoformat(),
        )
        assert replied_request == "runreq_test_002", f"unexpected replied request: {replied_request}"
        runtime_after_reply = load_runtime_state(projects_root, project_id)
        assert runtime_after_reply["requests"]["runreq_test_002"]["status"] == "replied"
        assert len(runtime_after_reply["processed"]) == 5, "mark_agent_replied must not alter processed ids"

        # Reminder candidates must respect age/cooldown and close after max reminders.
        future_31m = now + timedelta(minutes=31)
        candidates = iter_reminder_candidates(projects_root, project_id, now=future_31m)
        candidate_ids = {item["request_id"] for item in candidates}
        assert "runreq_test_001" in candidate_ids, "request should become reminder candidate after age threshold"
        assert "runreq_test_002" not in candidate_ids, "replied request should not be reminder candidate"

        reminder_t1 = (now + timedelta(minutes=31)).replace(microsecond=0).isoformat()
        reminder_t2 = (now + timedelta(minutes=92)).replace(microsecond=0).isoformat()
        reminder_t3 = (now + timedelta(minutes=153)).replace(microsecond=0).isoformat()

        status_1 = mark_request_reminded(
            projects_root, project_id, "runreq_test_001", reminded_at=reminder_t1, max_reminders=3
        )
        assert status_1["status"] == "reminded", "first reminder should keep request in reminded status"
        cool_candidates = iter_reminder_candidates(
            projects_root, project_id, now=now + timedelta(minutes=60)
        )
        cool_ids = {item["request_id"] for item in cool_candidates}
        assert "runreq_test_001" not in cool_ids, "cooldown should block immediate reminder repeats"

        status_2 = mark_request_reminded(
            projects_root, project_id, "runreq_test_001", reminded_at=reminder_t2, max_reminders=3
        )
        assert status_2["status"] == "reminded", "second reminder should still be reminded"
        status_3 = mark_request_reminded(
            projects_root, project_id, "runreq_test_001", reminded_at=reminder_t3, max_reminders=3
        )
        assert status_3["status"] == "closed", "third reminder should close request"
        runtime_after_close = load_runtime_state(projects_root, project_id)
        assert runtime_after_close["requests"]["runreq_test_001"]["closed_reason"] == "max_reminders_reached"

        post_close_candidates = iter_reminder_candidates(
            projects_root, project_id, now=now + timedelta(minutes=214)
        )
        post_close_ids = {item["request_id"] for item in post_close_candidates}
        assert "runreq_test_001" not in post_close_ids, "closed request must never be a reminder candidate"

    print("OK: auto-mode runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
