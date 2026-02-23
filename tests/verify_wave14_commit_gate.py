#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import MISSION_CRITICAL_GATE_FAILED_REASON, dispatch_once
from app.services.gatekeeper import (
    MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_INVALID,
    MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING,
    MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_EMPTY,
    MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_MISSING,
    evaluate_mission_critical_gate,
)


def _append(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _settings_payload() -> dict:
    return {
        "dispatch": {
            "scoring": {"enabled": True},
            "backpressure": {"enabled": True, "queue_target": 3, "max_actions_hard_cap": 5},
        },
        "mission_critical_gate": {
            "enabled": True,
            "trigger": "all_full_access",
            "approval_ref_pattern": "^APR-[A-Za-z0-9._-]+$",
            "required_evidence_sections": ["tests", "screenshots", "logs", "docs_updates"],
        },
    }


def main() -> int:
    settings = _settings_payload()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    gate_missing_approval = evaluate_mission_critical_gate(
        {
            "project_id": "cockpit",
            "agent_id": "agent-1",
            "action_scope": "full_access",
            "evidence": {
                "tests": ["tests/verify_wave14_commit_gate.py"],
                "screenshots": ["docs/reports/shot.png"],
                "logs": ["runs/log.txt"],
                "docs_updates": ["STATE.md"],
            },
        },
        settings=settings,
    )
    assert gate_missing_approval["applied"] is True
    assert gate_missing_approval["passed"] is False
    assert gate_missing_approval["code"] == MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING

    gate_invalid_approval = evaluate_mission_critical_gate(
        {
            "project_id": "cockpit",
            "agent_id": "agent-1",
            "action_scope": "full_access",
            "approval_ref": "BAD-1",
            "evidence": {
                "tests": ["tests/verify_wave14_commit_gate.py"],
                "screenshots": ["docs/reports/shot.png"],
                "logs": ["runs/log.txt"],
                "docs_updates": ["STATE.md"],
            },
        },
        settings=settings,
    )
    assert gate_invalid_approval["code"] == MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_INVALID

    gate_missing_sections = evaluate_mission_critical_gate(
        {
            "project_id": "cockpit",
            "agent_id": "agent-1",
            "action_scope": "full_access",
            "approval_ref": "APR-2026",
            "evidence": {"tests": ["tests/verify_wave14_commit_gate.py"]},
        },
        settings=settings,
    )
    assert gate_missing_sections["code"] == MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_MISSING
    assert "screenshots" in gate_missing_sections["missing_evidence_sections"]

    gate_empty_section = evaluate_mission_critical_gate(
        {
            "project_id": "cockpit",
            "agent_id": "agent-1",
            "action_scope": "full_access",
            "approval_ref": "APR-2026",
            "evidence": {
                "tests": ["tests/verify_wave14_commit_gate.py"],
                "screenshots": [],
                "logs": ["runs/log.txt"],
                "docs_updates": ["STATE.md"],
            },
        },
        settings=settings,
    )
    assert gate_empty_section["code"] == MISSION_CRITICAL_GATE_CODE_EVIDENCE_SECTION_EMPTY

    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        runs_dir = project_dir / "runs"
        requests_path = runs_dir / "requests.ndjson"
        settings_path = project_dir / "settings.json"
        _write_json(settings_path, settings)

        denied_payload = {
            "request_id": "req_denied",
            "project_id": project_id,
            "agent_id": "agent-1",
            "status": "queued",
            "source": "mention",
            "created_at": now,
            "action_scope": "full_access",
            "message": {"author": "operator", "text": "@agent-1 critical task", "mentions": ["agent-1"]},
        }
        allowed_payload = {
            "request_id": "req_allowed",
            "project_id": project_id,
            "agent_id": "agent-3",
            "status": "queued",
            "source": "mention",
            "created_at": now,
            "action_scope": "full_access",
            "approval_ref": "APR-200",
            "evidence": {
                "tests": ["tests/verify_wave14_commit_gate.py"],
                "screenshots": ["docs/reports/shot.png"],
                "logs": ["runs/log.txt"],
                "docs_updates": ["STATE.md"],
            },
            "message": {"author": "operator", "text": "@agent-3 critical task", "mentions": ["agent-3"]},
        }
        _append(requests_path, denied_payload)
        _append(requests_path, allowed_payload)

        result = dispatch_once(projects_root, project_id, max_actions=1)
        assert result.gate_blocked_count == 1, result
        assert result.dispatched_count == 1, result
        assert len(result.actions) == 1, result
        assert result.actions[0].request_id == "req_allowed"

        state_path = runs_dir / "auto_mode_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        runtime_requests = state.get("requests") if isinstance(state.get("requests"), dict) else {}
        denied_state = runtime_requests.get("req_denied") or {}
        assert denied_state.get("status") == "closed", denied_state
        assert denied_state.get("closed_reason") == MISSION_CRITICAL_GATE_FAILED_REASON, denied_state
        assert denied_state.get("completion_source") == MISSION_CRITICAL_GATE_FAILED_REASON, denied_state
        assert denied_state.get("error") == MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING, denied_state

        gate_report_path = runs_dir / "mission_critical_gate.ndjson"
        assert gate_report_path.exists(), "mission_critical_gate.ndjson should exist"
        rows = [json.loads(line) for line in gate_report_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) == 1, rows
        assert rows[0]["request_id"] == "req_denied", rows[0]
        assert rows[0]["code"] == MISSION_CRITICAL_GATE_CODE_APPROVAL_REF_MISSING, rows[0]
        assert rows[0]["closed_reason"] == MISSION_CRITICAL_GATE_FAILED_REASON, rows[0]

    print("OK: wave14 mission-critical commit gate verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
