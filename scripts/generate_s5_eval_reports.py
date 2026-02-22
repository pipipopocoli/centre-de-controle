#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.eval_policy import (
    CalibrationSample,
    EvalMetrics,
    OverrideRequest,
    compute_confusion_matrix,
    evaluate_release,
    load_threshold_policy,
    validate_calibration_targets,
    validate_threshold_policy,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _base_metrics() -> dict[str, object]:
    return {
        "suite": "B1",
        "pass_rate": 1.0,
        "critical_regressions": 0,
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


def build_eval_contracts_md(policy_version: str) -> str:
    return f"""# eval_contracts.md

## Stream
- Stream S5 L5 Eval harness
- Generated at: {_utc_now_iso()}
- Policy version: {policy_version}

## Registry schema
| field | type | required | notes |
|---|---|---|---|
| version | string | yes | non-empty version id |
| scenarios[] | list<object> | yes | sorted by scenario_id |
| scenario_id | string | yes | unique |
| suite_id | enum(B0,B1,B2,B3) | yes | benchmark lane |
| risk_tags | list<string> | yes | non-empty tags |
| active | boolean | yes | scenario enabled flag |
| owner_role | string | yes | accountable owner |

## Replay manifest schema
| field | type | required | notes |
|---|---|---|---|
| run_id | string | yes | replay run key |
| project_id | string | yes | project isolation key |
| git_sha | string | yes | candidate revision |
| scenario_profile | string | yes | suite profile |
| toolchain_hash | string | yes | deterministic runtime id |
| policy_version | string | yes | gate policy id |
| created_at | ISO-8601 | yes | event timestamp |
| seed | int/string | no | deterministic seed |
| trace_id | string | no | trace correlation id |

## Metrics schema
| field | type | required |
|---|---|---|
| suite | string | yes |
| pass_rate | float | yes |
| critical_regressions | int | yes |
| flake_delta_pp | float | yes |
| p95_runtime_min | float | yes |
| token_cost_usd | float | yes |
| policy_violation_count | int | yes |
| replay_fidelity_score | float | yes |
| baselines | object | yes |

## Verdict schema
| field | type |
|---|---|
| verdict | PASS \| SOFT_FAIL \| HARD_FAIL \| OVERRIDE_APPROVED |
| blocking_reasons | list<string> |
| soft_reasons | list<string> |
| policy_version | string |
| override_ref | string or null |

## Override audit schema
| field | type | required |
|---|---|---|
| run_id | string | yes |
| project_id | string | yes |
| actor | string | yes (@clems only for hard-fail override) |
| approval_ref | string | yes |
| rationale | string | yes |
| verdict_before | string | yes |
| verdict_after | string | yes |
| policy_version | string | yes |
| created_at | ISO-8601 | yes |

## CAP mapping
| capability_id | implementation | test gate |
|---|---|---|
| CAP-L5-001 | scenario_registry schema validation | benchmark catalog versioning pass |
| CAP-L5-002 | replay_manifest schema validation | replay bundle schema validation pass |
| CAP-L5-003 | threshold policy parser and validator | gate threshold parser and validation pass |
| CAP-L5-004 | confusion matrix + target validation | fp/fn confusion matrix target pass |
| CAP-L5-005 | release verdict policy engine | pass/soft_fail/hard_fail policy applied |
| CAP-L5-006 | override audit append with approval gate | override requires approval + rationale |

## Default threshold policy
- Hard rules:
  - critical_regressions > 0
  - pass_rate < 0.99 on B1
  - policy_violation_count > 0
  - replay_fidelity_score < 0.95
- Soft rules:
  - flake_delta_pp > 1.0
  - p95_runtime_min > baseline * 1.25
  - token_cost_usd > baseline * 1.20

## Override authority
- Hard-fail override requires `@clems`.
- `approval_ref` and rationale are mandatory.
- Every approved override must be appended to project-local audit NDJSON.
"""


def build_threshold_validation_md(policy_path: Path | None, command_evidence: str) -> tuple[str, bool]:
    policy = load_threshold_policy(policy_path)
    policy_errors = validate_threshold_policy(policy)

    vectors: list[tuple[str, EvalMetrics, OverrideRequest | None, str]] = []

    pass_metrics = EvalMetrics.from_dict(_base_metrics())
    vectors.append(("all_green", pass_metrics, None, "PASS"))

    soft_payload = dict(_base_metrics())
    soft_payload["flake_delta_pp"] = 1.5
    soft_metrics = EvalMetrics.from_dict(soft_payload)
    vectors.append(("soft_flake", soft_metrics, None, "SOFT_FAIL"))

    hard_payload = dict(_base_metrics())
    hard_payload["critical_regressions"] = 1
    hard_metrics = EvalMetrics.from_dict(hard_payload)
    vectors.append(("hard_critical", hard_metrics, None, "HARD_FAIL"))

    override = OverrideRequest(
        actor="@clems",
        approval_ref="APR-S5-001",
        rationale="emergency with rollback plan",
        run_id="run-s5-override-001",
    )
    vectors.append(("hard_with_override", hard_metrics, override, "OVERRIDE_APPROVED"))

    lines: list[str] = []
    lines.append("# threshold_validation_report.md")
    lines.append("")
    lines.append("## Stream")
    lines.append("- Stream S5 L5 Eval harness")
    lines.append(f"- Generated at: {_utc_now_iso()}")
    lines.append(f"- Policy version: {policy.policy_version}")
    lines.append(f"- Policy source: {policy_path if policy_path else 'default in-code baseline'}")
    lines.append(f"- Command evidence: `{command_evidence}`")
    lines.append("")
    lines.append("## Policy validation")
    if policy_errors:
        lines.append("- Status: FAIL")
        for error in policy_errors:
            lines.append(f"- {error}")
    else:
        lines.append("- Status: PASS")
        lines.append("- No parser/validator errors.")
    lines.append("")
    lines.append("## Rule-by-rule verdict vectors")
    lines.append("| vector_id | expected | actual | pass | blocking_reasons | soft_reasons |")
    lines.append("|---|---|---|---|---|---|")

    vector_pass_count = 0
    vector_fail_count = 0
    for vector_id, metrics, override_request, expected in vectors:
        verdict = evaluate_release(metrics=metrics, policy=policy, override=override_request)
        is_pass = verdict.verdict == expected
        if is_pass:
            vector_pass_count += 1
        else:
            vector_fail_count += 1
        blocking = "; ".join(verdict.blocking_reasons) if verdict.blocking_reasons else "-"
        soft = "; ".join(verdict.soft_reasons) if verdict.soft_reasons else "-"
        lines.append(
            f"| {vector_id} | {expected} | {verdict.verdict} | {'PASS' if is_pass else 'FAIL'} | {blocking} | {soft} |"
        )

    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Vector pass count: {vector_pass_count}")
    lines.append(f"- Vector fail count: {vector_fail_count}")

    report_ok = (len(policy_errors) == 0 and vector_fail_count == 0)
    lines.append(f"- Final status: {'PASS' if report_ok else 'FAIL'}")

    return "\n".join(lines) + "\n", report_ok


def build_calibration_md(policy_path: Path | None, command_evidence: str) -> tuple[str, bool]:
    policy = load_threshold_policy(policy_path)

    pass_samples = [CalibrationSample(actual_critical=True, predicted_hard_fail=True) for _ in range(19)]
    pass_samples += [CalibrationSample(actual_critical=True, predicted_hard_fail=False)]
    pass_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=True)]
    pass_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=False) for _ in range(19)]

    fail_samples = [CalibrationSample(actual_critical=True, predicted_hard_fail=True) for _ in range(5)]
    fail_samples += [CalibrationSample(actual_critical=True, predicted_hard_fail=False) for _ in range(5)]
    fail_samples += [CalibrationSample(actual_critical=False, predicted_hard_fail=False) for _ in range(20)]

    matrix_pass = compute_confusion_matrix(pass_samples)
    check_pass = validate_calibration_targets(matrix_pass, policy)

    matrix_fail = compute_confusion_matrix(fail_samples)
    check_fail = validate_calibration_targets(matrix_fail, policy)

    recommendation = "keep thresholds"
    if not check_pass.passed:
        recommendation = "tune thresholds"

    lines: list[str] = []
    lines.append("# calibration_report.md")
    lines.append("")
    lines.append("## Stream")
    lines.append("- Stream S5 L5 Eval harness")
    lines.append(f"- Generated at: {_utc_now_iso()}")
    lines.append(f"- Policy version: {policy.policy_version}")
    lines.append(f"- Command evidence: `{command_evidence}`")
    lines.append("")
    lines.append("## Targets")
    lines.append(f"- critical_precision_min: {policy.calibration_targets.get('critical_precision_min', 0.0):.2f}")
    lines.append(f"- critical_recall_min: {policy.calibration_targets.get('critical_recall_min', 0.0):.2f}")
    lines.append("")
    lines.append("## Matrix: passing calibration dataset")
    lines.append("| tp | fp | tn | fn | precision | recall | fpr | fnr | target_status |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    lines.append(
        "| "
        f"{matrix_pass.tp} | {matrix_pass.fp} | {matrix_pass.tn} | {matrix_pass.fn} | "
        f"{matrix_pass.precision:.4f} | {matrix_pass.recall:.4f} | {matrix_pass.fpr:.4f} | {matrix_pass.fnr:.4f} | "
        f"{'PASS' if check_pass.passed else 'FAIL'} |"
    )
    if check_pass.failures:
        for item in check_pass.failures:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("## Matrix: failing calibration dataset")
    lines.append("| tp | fp | tn | fn | precision | recall | fpr | fnr | target_status |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    lines.append(
        "| "
        f"{matrix_fail.tp} | {matrix_fail.fp} | {matrix_fail.tn} | {matrix_fail.fn} | "
        f"{matrix_fail.precision:.4f} | {matrix_fail.recall:.4f} | {matrix_fail.fpr:.4f} | {matrix_fail.fnr:.4f} | "
        f"{'PASS' if check_fail.passed else 'FAIL'} |"
    )
    if check_fail.failures:
        for item in check_fail.failures:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("## Recommendation")
    lines.append(f"- {recommendation}")

    report_ok = check_pass.passed and (not check_fail.passed)
    lines.append(f"- Validation outcome: {'PASS' if report_ok else 'FAIL'}")

    return "\n".join(lines) + "\n", report_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Stream S5 eval harness reports.")
    parser.add_argument("--project", required=True, help="Project id")
    parser.add_argument("--out", required=True, help="Output directory for generated reports")
    parser.add_argument("--policy", default="", help="Optional threshold policy JSON file")
    args = parser.parse_args()

    out_dir = Path(args.out).expanduser()
    policy_path = Path(args.policy).expanduser() if args.policy.strip() else None

    command_evidence = (
        ".venv/bin/python scripts/generate_s5_eval_reports.py "
        f"--project {args.project} --out {out_dir}"
        + (f" --policy {policy_path}" if policy_path else "")
    )

    policy = load_threshold_policy(policy_path)
    eval_contracts = build_eval_contracts_md(policy.policy_version)
    threshold_report, threshold_ok = build_threshold_validation_md(policy_path, command_evidence)
    calibration_report, calibration_ok = build_calibration_md(policy_path, command_evidence)

    _write(out_dir / "eval_contracts.md", eval_contracts)
    _write(out_dir / "threshold_validation_report.md", threshold_report)
    _write(out_dir / "calibration_report.md", calibration_report)

    print(f"Wrote: {out_dir / 'eval_contracts.md'}")
    print(f"Wrote: {out_dir / 'threshold_validation_report.md'}")
    print(f"Wrote: {out_dir / 'calibration_report.md'}")

    if not threshold_ok or not calibration_ok:
        print("One or more generated reports indicate FAIL status")
        return 1

    print("S5 reports generated successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
