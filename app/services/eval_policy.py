from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_OPERATORS = {">", ">=", "<", "<=", "=="}
ALLOWED_METRICS = {
    "pass_rate",
    "critical_regressions",
    "flake_delta_pp",
    "p95_runtime_min",
    "token_cost_usd",
    "policy_violation_count",
    "replay_fidelity_score",
}
ALLOWED_SUITES = {"B0", "B1", "B2", "B3"}
ALLOWED_RELATIVE_SEVERITY = {"hard", "soft"}


DEFAULT_POLICY_PAYLOAD: dict[str, Any] = {
    "policy_version": "l5-default-v1",
    "hard_rules": [
        {
            "metric": "critical_regressions",
            "operator": ">",
            "value": 0,
            "reason": "critical_regressions > 0",
        },
        {
            "metric": "pass_rate",
            "operator": "<",
            "value": 0.99,
            "suite": "B1",
            "reason": "pass_rate < 0.99 on B1",
        },
        {
            "metric": "policy_violation_count",
            "operator": ">",
            "value": 0,
            "reason": "policy_violation_count > 0",
        },
        {
            "metric": "replay_fidelity_score",
            "operator": "<",
            "value": 0.95,
            "reason": "replay_fidelity_score < 0.95",
        },
    ],
    "soft_rules": [
        {
            "metric": "flake_delta_pp",
            "operator": ">",
            "value": 1.0,
            "reason": "flake_delta_pp > 1.0",
        }
    ],
    "relative_rules": [
        {
            "metric": "p95_runtime_min",
            "operator": ">",
            "baseline_key": "p95_runtime_min",
            "factor": 1.25,
            "severity": "soft",
            "reason": "p95_runtime_min > baseline * 1.25",
        },
        {
            "metric": "token_cost_usd",
            "operator": ">",
            "baseline_key": "token_cost_usd",
            "factor": 1.20,
            "severity": "soft",
            "reason": "token_cost_usd > baseline * 1.20",
        },
    ],
    "calibration_targets": {
        "critical_precision_min": 0.90,
        "critical_recall_min": 0.95,
    },
}


@dataclass(frozen=True)
class ThresholdRule:
    metric: str
    operator: str
    value: float | None
    suite: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class RelativeRule:
    metric: str
    operator: str
    baseline_key: str
    factor: float | None
    severity: str
    reason: str = ""


@dataclass(frozen=True)
class ThresholdPolicy:
    policy_version: str
    hard_rules: list[ThresholdRule]
    soft_rules: list[ThresholdRule]
    relative_rules: list[RelativeRule]
    calibration_targets: dict[str, float]


@dataclass(frozen=True)
class EvalMetrics:
    suite: str
    pass_rate: float
    critical_regressions: int
    flake_delta_pp: float
    p95_runtime_min: float
    token_cost_usd: float
    policy_violation_count: int
    replay_fidelity_score: float
    baselines: dict[str, float]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvalMetrics":
        if not isinstance(payload, dict):
            payload = {}
        baselines_raw = payload.get("baselines")
        baselines: dict[str, float] = {}
        if isinstance(baselines_raw, dict):
            for key, value in baselines_raw.items():
                number = _to_float(value)
                if number is not None:
                    baselines[str(key)] = number

        return cls(
            suite=str(payload.get("suite") or "B1"),
            pass_rate=float(_to_float(payload.get("pass_rate"), default=1.0)),
            critical_regressions=int(_to_int(payload.get("critical_regressions"), default=0)),
            flake_delta_pp=float(_to_float(payload.get("flake_delta_pp"), default=0.0)),
            p95_runtime_min=float(_to_float(payload.get("p95_runtime_min"), default=0.0)),
            token_cost_usd=float(_to_float(payload.get("token_cost_usd"), default=0.0)),
            policy_violation_count=int(_to_int(payload.get("policy_violation_count"), default=0)),
            replay_fidelity_score=float(_to_float(payload.get("replay_fidelity_score"), default=1.0)),
            baselines=baselines,
        )


@dataclass(frozen=True)
class OverrideRequest:
    actor: str
    approval_ref: str
    rationale: str
    run_id: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OverrideRequest":
        if not isinstance(payload, dict):
            payload = {}
        return cls(
            actor=str(payload.get("actor") or ""),
            approval_ref=str(payload.get("approval_ref") or ""),
            rationale=str(payload.get("rationale") or ""),
            run_id=str(payload.get("run_id") or ""),
        )


@dataclass(frozen=True)
class EvalVerdict:
    verdict: str
    blocking_reasons: list[str]
    soft_reasons: list[str]
    policy_version: str
    override_ref: str | None = None


@dataclass(frozen=True)
class CalibrationSample:
    actual_critical: bool
    predicted_hard_fail: bool


@dataclass(frozen=True)
class ConfusionMatrix:
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    fpr: float
    fnr: float


@dataclass(frozen=True)
class CalibrationCheck:
    passed: bool
    precision: float
    recall: float
    targets: dict[str, float]
    failures: list[str]


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_threshold_rule(payload: dict[str, Any]) -> ThresholdRule:
    metric = str(payload.get("metric") or "")
    operator = str(payload.get("operator") or "")
    value = _to_float(payload.get("value"))
    suite_raw = payload.get("suite")
    suite = str(suite_raw) if isinstance(suite_raw, str) and suite_raw.strip() else None
    reason = str(payload.get("reason") or f"{metric} {operator} {value}")
    return ThresholdRule(metric=metric, operator=operator, value=value, suite=suite, reason=reason)


def _parse_relative_rule(payload: dict[str, Any]) -> RelativeRule:
    metric = str(payload.get("metric") or "")
    operator = str(payload.get("operator") or "")
    baseline_key = str(payload.get("baseline_key") or "")
    factor = _to_float(payload.get("factor"))
    severity = str(payload.get("severity") or "soft")
    reason = str(payload.get("reason") or f"{metric} {operator} baseline({baseline_key}) * {factor}")
    return RelativeRule(
        metric=metric,
        operator=operator,
        baseline_key=baseline_key,
        factor=factor,
        severity=severity,
        reason=reason,
    )


def parse_threshold_policy(payload: dict[str, Any]) -> ThresholdPolicy:
    if not isinstance(payload, dict):
        payload = {}

    hard_raw = payload.get("hard_rules")
    soft_raw = payload.get("soft_rules")
    relative_raw = payload.get("relative_rules")
    targets_raw = payload.get("calibration_targets")

    hard_rules = [
        _parse_threshold_rule(item)
        for item in hard_raw
        if isinstance(item, dict)
    ] if isinstance(hard_raw, list) else []

    soft_rules = [
        _parse_threshold_rule(item)
        for item in soft_raw
        if isinstance(item, dict)
    ] if isinstance(soft_raw, list) else []

    relative_rules = [
        _parse_relative_rule(item)
        for item in relative_raw
        if isinstance(item, dict)
    ] if isinstance(relative_raw, list) else []

    targets: dict[str, float] = {}
    if isinstance(targets_raw, dict):
        for key, value in targets_raw.items():
            number = _to_float(value)
            if number is not None:
                targets[str(key)] = number

    return ThresholdPolicy(
        policy_version=str(payload.get("policy_version") or ""),
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        relative_rules=relative_rules,
        calibration_targets=targets,
    )


def load_threshold_policy(path: Path | None = None) -> ThresholdPolicy:
    merged = copy.deepcopy(DEFAULT_POLICY_PAYLOAD)
    if path is not None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("threshold policy file must contain a JSON object")
        for key, value in payload.items():
            merged[str(key)] = value
    return parse_threshold_policy(merged)


def validate_threshold_policy(policy: ThresholdPolicy) -> list[str]:
    errors: list[str] = []

    if not policy.policy_version.strip():
        errors.append("policy_version is required")

    for bucket_name, rules in (("hard_rules", policy.hard_rules), ("soft_rules", policy.soft_rules)):
        for idx, rule in enumerate(rules):
            prefix = f"{bucket_name}[{idx}]"
            if rule.metric not in ALLOWED_METRICS:
                errors.append(f"{prefix}.metric must be one of {sorted(ALLOWED_METRICS)}")
            if rule.operator not in ALLOWED_OPERATORS:
                errors.append(f"{prefix}.operator must be one of {sorted(ALLOWED_OPERATORS)}")
            if rule.value is None or math.isnan(rule.value):
                errors.append(f"{prefix}.value must be numeric")
            if rule.suite is not None and rule.suite not in ALLOWED_SUITES:
                errors.append(f"{prefix}.suite must be one of {sorted(ALLOWED_SUITES)}")

    for idx, rule in enumerate(policy.relative_rules):
        prefix = f"relative_rules[{idx}]"
        if rule.metric not in ALLOWED_METRICS:
            errors.append(f"{prefix}.metric must be one of {sorted(ALLOWED_METRICS)}")
        if rule.operator not in ALLOWED_OPERATORS:
            errors.append(f"{prefix}.operator must be one of {sorted(ALLOWED_OPERATORS)}")
        if not rule.baseline_key.strip():
            errors.append(f"{prefix}.baseline_key is required")
        if rule.factor is None or math.isnan(rule.factor) or rule.factor <= 0:
            errors.append(f"{prefix}.factor must be > 0")
        if rule.severity not in ALLOWED_RELATIVE_SEVERITY:
            errors.append(f"{prefix}.severity must be one of {sorted(ALLOWED_RELATIVE_SEVERITY)}")

    required_targets = ("critical_precision_min", "critical_recall_min")
    for key in required_targets:
        value = policy.calibration_targets.get(key)
        if value is None:
            errors.append(f"calibration_targets.{key} is required")
            continue
        if value < 0 or value > 1:
            errors.append(f"calibration_targets.{key} must be between 0 and 1")

    return errors


def _compare(left: float, operator: str, right: float) -> bool:
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == "==":
        return left == right
    return False


def _metric_value(metrics: EvalMetrics, metric_name: str) -> float:
    return float(getattr(metrics, metric_name))


def _override_is_valid(override: OverrideRequest | None) -> bool:
    if override is None:
        return False
    if override.actor.strip() != "@clems":
        return False
    if not override.approval_ref.strip():
        return False
    if not override.rationale.strip():
        return False
    if not override.run_id.strip():
        return False
    return True


def evaluate_release(
    metrics: EvalMetrics,
    policy: ThresholdPolicy,
    override: OverrideRequest | None = None,
) -> EvalVerdict:
    policy_errors = validate_threshold_policy(policy)
    if policy_errors:
        return EvalVerdict(
            verdict="HARD_FAIL",
            blocking_reasons=[f"invalid policy: {err}" for err in policy_errors],
            soft_reasons=[],
            policy_version=policy.policy_version or "unknown",
            override_ref=None,
        )

    blocking_reasons: list[str] = []
    soft_reasons: list[str] = []

    for rule in policy.hard_rules:
        if rule.suite is not None and rule.suite != metrics.suite:
            continue
        if rule.value is None:
            continue
        value = _metric_value(metrics, rule.metric)
        if _compare(value, rule.operator, float(rule.value)):
            blocking_reasons.append(rule.reason)

    for rule in policy.soft_rules:
        if rule.suite is not None and rule.suite != metrics.suite:
            continue
        if rule.value is None:
            continue
        value = _metric_value(metrics, rule.metric)
        if _compare(value, rule.operator, float(rule.value)):
            soft_reasons.append(rule.reason)

    for rule in policy.relative_rules:
        baseline = metrics.baselines.get(rule.baseline_key)
        if baseline is None:
            message = f"missing baseline: {rule.baseline_key}"
            if rule.severity == "hard":
                blocking_reasons.append(message)
            else:
                soft_reasons.append(message)
            continue
        if rule.factor is None:
            continue
        value = _metric_value(metrics, rule.metric)
        threshold = float(baseline) * float(rule.factor)
        if _compare(value, rule.operator, threshold):
            if rule.severity == "hard":
                blocking_reasons.append(rule.reason)
            else:
                soft_reasons.append(rule.reason)

    if blocking_reasons:
        if _override_is_valid(override):
            return EvalVerdict(
                verdict="OVERRIDE_APPROVED",
                blocking_reasons=blocking_reasons,
                soft_reasons=soft_reasons,
                policy_version=policy.policy_version,
                override_ref=override.approval_ref,
            )
        return EvalVerdict(
            verdict="HARD_FAIL",
            blocking_reasons=blocking_reasons,
            soft_reasons=soft_reasons,
            policy_version=policy.policy_version,
            override_ref=None,
        )

    if soft_reasons:
        return EvalVerdict(
            verdict="SOFT_FAIL",
            blocking_reasons=[],
            soft_reasons=soft_reasons,
            policy_version=policy.policy_version,
            override_ref=None,
        )

    return EvalVerdict(
        verdict="PASS",
        blocking_reasons=[],
        soft_reasons=[],
        policy_version=policy.policy_version,
        override_ref=None,
    )


def compute_confusion_matrix(samples: list[CalibrationSample]) -> ConfusionMatrix:
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for sample in samples:
        if sample.actual_critical and sample.predicted_hard_fail:
            tp += 1
        elif not sample.actual_critical and sample.predicted_hard_fail:
            fp += 1
        elif not sample.actual_critical and not sample.predicted_hard_fail:
            tn += 1
        else:
            fn += 1

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return ConfusionMatrix(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=precision,
        recall=recall,
        fpr=fpr,
        fnr=fnr,
    )


def validate_calibration_targets(matrix: ConfusionMatrix, policy: ThresholdPolicy) -> CalibrationCheck:
    failures: list[str] = []
    targets = {
        "critical_precision_min": policy.calibration_targets.get("critical_precision_min", 0.0),
        "critical_recall_min": policy.calibration_targets.get("critical_recall_min", 0.0),
    }

    if matrix.precision < targets["critical_precision_min"]:
        failures.append(
            "precision below target "
            f"({matrix.precision:.4f} < {targets['critical_precision_min']:.4f})"
        )
    if matrix.recall < targets["critical_recall_min"]:
        failures.append(
            "recall below target "
            f"({matrix.recall:.4f} < {targets['critical_recall_min']:.4f})"
        )

    return CalibrationCheck(
        passed=(len(failures) == 0),
        precision=matrix.precision,
        recall=matrix.recall,
        targets=targets,
        failures=failures,
    )
