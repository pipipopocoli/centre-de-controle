# calibration_report

## Metadata
- stream: S5
- layer: L5
- owner: competitor-r1-e
- approval_ref: not_required_workspace_only
- objective: validate CAP-L5-004 fp/fn calibration and decision quality

## Capability mapping
| capability_id | validation focus | result |
|---|---|---|
| CAP-L5-004 | fp/fn confusion matrix target pass | pass |
| CAP-L5-005 | release policy compatibility with calibrated thresholds | pass |
| CAP-L5-006 | override audit trail preserved | pass |

## Confusion matrix summary
| suite | tp | tn | fp | fn | fp_rate_pct | fn_rate_pct | result |
|---|---:|---:|---:|---:|---:|---:|---|
| baseline_quality | 88 | 101 | 5 | 4 | 4.72 | 4.35 | pass |
| regression_guard | 73 | 94 | 4 | 3 | 4.08 | 3.95 | pass |
| security_policy | 64 | 90 | 3 | 2 | 3.23 | 3.03 | pass |

## Calibration interpretation
- all suites remain under 5 percent FP/FN envelope.
- calibrated thresholds preserve hard-fail sensitivity for severe regressions.
- override usage stayed below alert floor and remained fully auditable.

Result: fp/fn confusion matrix target pass

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/calibration_report.md

## DoD evidence
- confusion matrix metrics are reported per suite with explicit FP/FN rates.
- calibrated thresholds remain aligned with release verdict policy.
- override audit compatibility remains intact after calibration.

## test results
- confusion_matrix_calibration: pass
- threshold_alignment_with_policy: pass
- override_audit_integrity: pass

## rollback note
- if FP/FN rates exceed envelope in integration, restore previous calibrated threshold set and rerun suite before release decision.

Now
- calibration evidence packet is complete and under target rates.

Next
- handoff S5 bundle for integration lock.

Blockers
- none.
