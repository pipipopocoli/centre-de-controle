#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import CODEX_ONLY_OUTAGE_PAUSED_REASON, dispatch_once


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

        _write_json(
            project_dir / "settings.json",
            {
                "dispatch": {
                    "scoring": {"enabled": False},
                    "backpressure": {"enabled": True, "queue_target": 3, "max_actions_hard_cap": 5},
                },
                "outage_mode": {
                    "codex_only_enabled": True,
                    "allowed_platforms": ["codex"],
                    "allowed_agents": ["victor", "nova", "agent-3"],
                },
                "credit_guard": {
                    "enabled": True,
                    "max_actions_effective": 1,
                },
            },
        )

        _write_json(
            project_dir / "agents" / "registry.json",
            {
                "victor": {
                    "agent_id": "victor",
                    "name": "Victor",
                    "engine": "CDX",
                    "platform": "codex",
                    "level": 1,
                    "lead_id": "clems",
                    "role": "backend_lead",
                    "skills": [],
                },
                "nova": {
                    "agent_id": "nova",
                    "name": "Nova",
                    "engine": "AG",
                    "platform": "antigravity",
                    "level": 1,
                    "lead_id": "clems",
                    "role": "creative_science_lead",
                    "skills": [],
                },
                "leo": {
                    "agent_id": "leo",
                    "name": "Leo",
                    "engine": "AG",
                    "platform": "antigravity",
                    "level": 1,
                    "lead_id": "clems",
                    "role": "ui_lead",
                    "skills": [],
                },
            },
        )

        _append_ndjson(
            runs_dir / "requests.ndjson",
            {
                "request_id": "req_victor",
                "project_id": project_id,
                "agent_id": "victor",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-24T00:00:00+00:00",
                "message": {"text": "Ping @victor"},
            },
        )
        _append_ndjson(
            runs_dir / "requests.ndjson",
            {
                "request_id": "req_nova",
                "project_id": project_id,
                "agent_id": "nova",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-24T00:00:01+00:00",
                "message": {"text": "Ping @nova"},
            },
        )
        _append_ndjson(
            runs_dir / "requests.ndjson",
            {
                "request_id": "req_leo",
                "project_id": project_id,
                "agent_id": "leo",
                "status": "queued",
                "source": "mention",
                "created_at": "2026-02-24T00:00:02+00:00",
                "message": {"text": "Ping @leo"},
            },
        )

        result = dispatch_once(projects_root, project_id, max_actions=5)
        assert result.dispatched_count == 2, result
        assert len(result.actions) == 1, result
        assert all(action.platform == "codex" for action in result.actions), result

        state_path = runs_dir / "auto_mode_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        requests = state.get("requests") if isinstance(state.get("requests"), dict) else {}
        assert requests["req_victor"]["status"] == "dispatched", requests
        assert requests["req_nova"]["status"] == "dispatched", requests
        assert requests["req_leo"]["status"] == "closed", requests
        assert requests["req_leo"]["closed_reason"] == CODEX_ONLY_OUTAGE_PAUSED_REASON, requests

        leo_inbox = runs_dir / "inbox" / "leo.ndjson"
        assert not leo_inbox.exists(), "leo inbox should remain untouched in codex-only outage mode"

    print("OK: wave16 codex-only outage mode verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
