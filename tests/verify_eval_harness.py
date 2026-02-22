#!/usr/bin/env python3
"""Eval harness verification for CAP-L5-001..CAP-L5-006."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.eval_policy import (  # noqa: E402
    CalibrationSample,
    EvalMetrics,
    OverrideRequest,
    compute_confusion_matrix,
    evaluate_release,
    load_threshold_policy,
    validate_calibration_targets,
    validate_threshold_policy,
)
from app.services.eval_registry import (  # noqa: E402
    validate_replay_manifest,
    validate_scenario_registry,
)


def _assert_has(errors: list[str], expected: str) -> None:
    assert any(expected in item for item in errors), f"missing error fragment: {expected}"


def test_scenario_registry_validation() -> None:
    valid_payload = {
        "version": "registry-v1",
        "scenarios": [
            {
                "scenario_id": "scn-001",
                "suite_id": "B1",
                "risk_tags": ["core"],
                "active": True,
                "owner_role": "qa-lead",
            },
            {
                "scenario_id": "scn-002",
                "suite_id": "B2",
                "risk_tags": ["incident"],
                "active": True,
                "owner_role": "qa-lead",
            },
        ],
    }
    assert validate_scenario_registry(valid_payload) == []

    invalid_payload = {
        "version": "",
        "scenarios": [
            {
                "scenario_id": "scn-010",
                "suite_id": "B9",
                "risk_tags": [""],
                "active": "yes",
                "owner_role": "",
            },
            {
                "scenario_id": "scn-010",
                "suite_id": "B1",
                "risk_tags": ["ok"],
                "active": True,
                "owner_role": "qa",
            },
        ],
    }
    errors = validate_scenario_registry(invalid_payload)
    _assert_has(errors, "version is required")
    _assert_has(errors, "duplicate scenario_id")
    _assert_has(errors, "suite_id must be one of")
    _assert_has(errors, "risk_tags must be a list")
    _assert_has(errors, "active must be a boolean")
    _assert_has(errors, "owner_role must be a non-empty string")


def test_replay_manifest_validation() -> None:
    valid_manifest = {
        "run_id": "run-1",
        "project_id": "cockpit",
        "git_sha": "abc123",
        "scenario_profile": "B1",
        "toolchain_hash": "tool-1",
        "policy_version": "l5-default-v1",
        "created_at": "2026-02-19T04:00:00+00:00",
        "seed": 42,
        "trace_id": "trace-1",
    }
    assert validate_replay_manifest(valid_manifest) == []

    invalid_manifest = {
        "run_id": "",
        "project_id": "",
        "git_sha": "",
        "scenario_profile": "",
        "toolchain_hash": "",
        "policy_version": "",
        "created_at": "not-an-iso",
        "seed": [],
        "trace_id": "",
    }
    errors = validate_replay_manifest(invalid_manifest)
    _assert_has(errors, "run_id is required")
    _assert_has(errors, "created_at must be ISO-8601")
    _assert_has(errors, "seed must be int, string, or null")
    _assert_has(errors, "trace_id must be a non-empty string")


def test_threshold_policy_parser_validation() -> None:
    default_policy = load_threshold_policy()
    assert validate_threshold_policy(default_policy) == []

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad_policy.json"
        path.write_text(
            json.dumps(
                {
                    "policy_version": "custom-invalid",
                    "hard_rules": [
                        {
                            "metric": "critical_regressions",
                            "operator": "!=",
                            "value": 0,
                        }
                    ],
                    "soft_rules": [
                        {
                            "operator": ">",
                            "value": 1.0,
                        }
                    ],
                    "relative_rules": [
                        {
                            "metric": "p95_runtime_min",
                            "operator": ">",
                            "baseline_key": "",
                            "factor": 1.1,
                            "severity": "soft",
                        }
                    ],
                    "calibration_targets": {
                        "critical_precision_min": 0.90,
                    },
                }
            ),
            encoding="utf-8",
        )
        invalid_policy = load_threshold_policy(path)

    errors = validate_threshold_policy(invalid_policy)
    _assert_has(errors, "operator must be one of")
    _assert_has(errors, "metric must be one of")
    _assert_has(errors, "baseline_key is required")
    _assert_has(errors, "critical_recall_min is required")


def test_release_verdict_vectors() -> None:
    policy = load_threshold_policy()

    pass_metrics = EvalMetrics.from_dict(
        {
            "suite": "B1",
            "pass_rate": 1.0,
            "critical_regressions": 0,
            "flake_delta_pp": 0.2,
            "p95_runtime_min": 10.0,
            "token_cost_usd": 10.0,
            "policy_violation_count": 0,
            "replay_fidelity_score": 0.98,
            "baselines": {
                "p95_runtime_min": 10.0,
                "token_cost_usd": 10.0,
            },
        }
    )
    assert evaluate_release(pass_metrics, policy).verdict == "PASS"

    soft_metrics = EvalMetrics.from_dict(
        {
            "suite": "B1",
            "pass_rate": 1.0,
            "critical_regressions": 0,
            "flake_delta_pp": 1.5,
            "p95_runtime_min": 10.0,
            "token_cost_usd": 10.0,
            "policy_violation_count": 0,
            "replay_fidelity_score": 0.98,
            "baselines": {
                "p95_runtime_min": 10.0,
                "token_cost_usd": 10.0,
            },
        }
    )
    assert evaluate_release(soft_metrics, policy).verdict == "SOFT_FAIL"

    hard_metrics = EvalMetrics.from_dict(
        {
            "suite": "B1",
            "pass_rate": 1.0,
            "critical_regressions": 1,
            "flake_delta_pp": 0.0,
            "p95_runtime_min": 10.0,
            "token_cost_usd": 10.0,
            "policy_violation_count": 0,
            "replay_fidelity_score": 0.98,
            "baselines": {
                "p95_runtime_min": 10.0,
                "token_cost_usd": 10.0,
            },
        }
    )
    assert evaluate_release(hard_metrics, policy).verdict == "HARD_FAIL"

    override = OverrideRequest(
        actor="@clems",
        approval_ref="APR-123",
        rationale="incident accepted",
        run_id="run-override-1",
    )
    assert evaluate_release(hard_metrics, policy, override=override).verdict == "OVERRIDE_APPROVED"


def test_calibration_vectors() -> None:
    policy = load_threshold_policy()

    pass_samples = [CalibrationSample(actual_critical=True, predicted_hard_fail=True) for _ in range(19)]
    pass_samples += [CalibrationSample(actual_critical=True, predicted_hard_fail=False)]
    pass_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=True)]
    pass_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=False) for _ in range(19)]

    matrix_pass = compute_confusion_matrix(pass_samples)
    check_pass = validate_calibration_targets(matrix_pass, policy)
    assert check_pass.passed is True

    fail_samples = [CalibrationSample(actual_critical=True, predicted_hard_fail=True) for _ in range(5)]
    fail_samples += [CalibrationSample(actual_critical=True, predicted_hard_fail=False) for _ in range(5)]
    fail_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=False) for _ in range(20)]

    matrix_fail = compute_confusion_matrix(fail_samples)
    check_fail = validate_calibration_targets(matrix_fail, policy)
    assert check_fail.passed is False
    _assert_has(check_fail.failures, "recall below target")


def main() -> int:
    tests = [
        test_scenario_registry_validation,
        test_replay_manifest_validation,
        test_threshold_policy_parser_validation,
        test_release_verdict_vectors,
        test_calibration_vectors,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {test.__name__}: {exc}")

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: eval harness verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
