#!/usr/bin/env python3
"""Gatekeeper eval integration verification for CAP-L5-005 and CAP-L5-006."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.gatekeeper import check_dispatch  # noqa: E402


def _hard_fail_metrics() -> dict[str, object]:
    return {
        "suite": "B1",
        "pass_rate": 1.0,
        "critical_regressions": 2,
        "flake_delta_pp": 0.0,
        "p95_runtime_min": 10.0,
        "token_cost_usd": 10.0,
        "policy_violation_count": 0,
        "replay_fidelity_score": 0.99,
        "baselines": {
            "p95_runtime_min": 10.0,
            "token_cost_usd": 10.0,
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        (projects_root / project_id / "runs").mkdir(parents=True, exist_ok=True)

        base_request = {
            "project_id": project_id,
            "agent_id": "agent-5",
            "request_id": "runreq-eval-1",
        }

        # non-eval path still passes
        passed, reason = check_dispatch(base_request, project_context=None)
        assert passed is True, f"non-eval request should pass, got: {reason}"

        # hard-fail without override must block
        hard_fail_request = {
            **base_request,
            "eval_payload": {
                "metrics": _hard_fail_metrics(),
            },
        }
        passed, reason = check_dispatch(hard_fail_request, project_context={"projects_root": str(projects_root)})
        assert passed is False, "hard-fail without override must be blocked"
        assert "Eval gate blocked dispatch" in reason

        # invalid actor override must block
        invalid_override_request = {
            **base_request,
            "eval_payload": {
                "metrics": _hard_fail_metrics(),
                "override": {
                    "actor": "@victor",
                    "approval_ref": "APR-INVALID",
                    "rationale": "not authorized",
                    "run_id": "run-hard-2",
                },
            },
        }
        passed, reason = check_dispatch(
            invalid_override_request,
            project_context={"projects_root": str(projects_root)},
        )
        assert passed is False, "override by non-clems actor must be blocked"
        assert "Eval gate blocked dispatch" in reason

        # valid @clems override passes and writes audit
        valid_override_request = {
            **base_request,
            "eval_payload": {
                "metrics": _hard_fail_metrics(),
                "override": {
                    "actor": "@clems",
                    "approval_ref": "APR-VALID-001",
                    "rationale": "emergency release with rollback ready",
                    "run_id": "run-hard-3",
                },
            },
        }
        passed, reason = check_dispatch(
            valid_override_request,
            project_context={"projects_root": str(projects_root)},
        )
        assert passed is True, f"valid clems override should pass, got: {reason}"
        assert "OVERRIDE_APPROVED" in reason

        audit_path = projects_root / project_id / "runs" / "eval_override_audit.ndjson"
        assert audit_path.exists(), "override audit file must be created"
        lines = [line for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == 1, "expected one audit entry"
        payload = json.loads(lines[0])
        assert payload["approval_ref"] == "APR-VALID-001"
        assert payload["actor"] == "@clems"
        assert payload["verdict_before"] == "HARD_FAIL"
        assert payload["verdict_after"] == "OVERRIDE_APPROVED"

    print("OK: gatekeeper eval integration verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
