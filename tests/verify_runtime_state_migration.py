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


def _write_legacy_state(path: Path, request_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "processed": request_ids,
                "counters": {"ticks": 42, "last_tick_at": "2026-02-12T11:00:00+00:00"},
                "updated_at": "2026-02-12T00:00:00+00:00",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        runs_dir = projects_root / project_id / "runs"
        requests_path = runs_dir / "requests.ndjson"
        state_path = runs_dir / "auto_mode_state.json"

        request_external = "runreq_legacy_external"
        request_reminder = "runreq_legacy_reminder"
        request_internal = "runreq_legacy_internal"
        request_missing = "runreq_legacy_missing"

        _write_ndjson(
            requests_path,
            {
                "request_id": request_external,
                "project_id": project_id,
                "agent_id": "agent-7",
                "source": "mention",
                "created_at": "2026-02-12T10:00:00+00:00",
            },
        )
        _write_ndjson(
            requests_path,
            {
                "request_id": request_reminder,
                "project_id": project_id,
                "agent_id": "agent-7",
                "source": "reminder",
                "created_at": "2026-02-12T10:05:00+00:00",
            },
        )
        _write_ndjson(
            requests_path,
            {
                "request_id": request_internal,
                "project_id": project_id,
                "agent_id": "clems",
                "source": "mention",
                "created_at": "2026-02-12T10:06:00+00:00",
            },
        )

        _write_legacy_state(state_path, [request_external, request_reminder, request_internal, request_missing])

        result = dispatch_once(projects_root, project_id, max_actions=0)
        assert result.dispatched_count == 0, "legacy processed rows must not redispatch"

        payload = json.loads(state_path.read_text(encoding="utf-8"))
        assert payload.get("schema_version") == 3, "state must be migrated to schema v3"

        processed = payload.get("processed")
        assert isinstance(processed, list)
        requests_map = payload.get("requests")
        assert isinstance(requests_map, dict)
        counters = payload.get("counters")
        assert isinstance(counters, dict)
        assert counters.get("ticks") == 42

        processed_set = set(processed)
        assert processed_set <= set(requests_map.keys()), "every processed id must exist in runtime requests map"

        external_row = requests_map[request_external]
        assert external_row.get("status") == "closed"
        assert external_row.get("closed_reason") == "legacy_processed"

        reminder_row = requests_map[request_reminder]
        assert reminder_row.get("status") == "closed"
        assert reminder_row.get("closed_reason") == "reminder_event"

        internal_row = requests_map[request_internal]
        assert internal_row.get("status") == "closed"
        assert internal_row.get("closed_reason") == "internal_agent_not_dispatchable"

        missing_row = requests_map[request_missing]
        assert missing_row.get("status") == "closed"
        assert missing_row.get("closed_reason") == "legacy_processed"

    print("OK: runtime state migration verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
