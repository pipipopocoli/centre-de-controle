# threshold_validation_report.md

## Stream
- Stream S5 L5 Eval harness
- Generated at: 2026-02-18T20:38:59+00:00
- Policy version: l5-default-v1
- Policy source: default in-code baseline
- Command evidence: `.venv/bin/python scripts/generate_s5_eval_reports.py --project cockpit --out /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/S5`

## Policy validation
- Status: PASS
- No parser/validator errors.

## Rule-by-rule verdict vectors
| vector_id | expected | actual | pass | blocking_reasons | soft_reasons |
|---|---|---|---|---|---|
| all_green | PASS | PASS | PASS | - | - |
| soft_flake | SOFT_FAIL | SOFT_FAIL | PASS | - | flake_delta_pp > 1.0 |
| hard_critical | HARD_FAIL | HARD_FAIL | PASS | critical_regressions > 0 | - |
| hard_with_override | OVERRIDE_APPROVED | OVERRIDE_APPROVED | PASS | critical_regressions > 0 | - |

## Summary
- Vector pass count: 4
- Vector fail count: 0
- Final status: PASS
