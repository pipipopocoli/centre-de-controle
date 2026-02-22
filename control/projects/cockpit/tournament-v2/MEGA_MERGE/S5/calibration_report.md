# calibration_report.md

## Stream
- Stream S5 L5 Eval harness
- Generated at: 2026-02-18T20:38:59+00:00
- Policy version: l5-default-v1
- Command evidence: `.venv/bin/python scripts/generate_s5_eval_reports.py --project cockpit --out /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/S5`

## Targets
- critical_precision_min: 0.90
- critical_recall_min: 0.95

## Matrix: passing calibration dataset
| tp | fp | tn | fn | precision | recall | fpr | fnr | target_status |
|---|---|---|---|---|---|---|---|---|
| 19 | 1 | 19 | 1 | 0.9500 | 0.9500 | 0.0500 | 0.0500 | PASS |

## Matrix: failing calibration dataset
| tp | fp | tn | fn | precision | recall | fpr | fnr | target_status |
|---|---|---|---|---|---|---|---|---|
| 5 | 0 | 20 | 5 | 1.0000 | 0.5000 | 0.0000 | 0.5000 | FAIL |
- recall below target (0.5000 < 0.9500)

## Recommendation
- keep thresholds
- Validation outcome: PASS
