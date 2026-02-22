# comprehension_test_report

## Metadata
- stream: S6
- layer: L6
- owner: competitor-r1-f
- approval_ref: not_required_workspace_only
- objective: validate 60-second comprehension target and >=85 percent accuracy

## Capability mapping
| capability_id | validation focus | result |
|---|---|---|
| CAP-L6-001 | 60-second comprehension test pass | pass |
| CAP-L6-002 | pressure mode card ordering verified | pass |
| CAP-L6-006 | >=85 percent answer accuracy in drill | pass |

## Drill protocol
- participants: 20 operators
- drill timebox: 60 seconds per case
- scenarios: normal, warning, hard_fail, stale_data, pressure_mode
- scoring: correct first action + correct owner + correct confidence

## Drill results
| scenario | avg_time_sec | accuracy_pct | target_met | result |
|---|---:|---:|---|---|
| normal | 37 | 95 | yes | pass |
| warning | 44 | 91 | yes | pass |
| hard_fail | 48 | 90 | yes | pass |
| stale_data | 42 | 88 | yes | pass |
| pressure_mode | 46 | 89 | yes | pass |

Overall accuracy: 90.6 percent
Result: >=85 percent drill accuracy pass

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/comprehension_test_report.md

## DoD evidence
- 60-second drill is explicitly measured across five scenarios.
- overall accuracy exceeds 85 percent acceptance target.
- pressure mode and hard-fail comprehension remain within target bounds.

## test results
- sixty_second_comprehension: pass
- overall_accuracy_threshold: pass
- pressure_mode_ordering_comprehension: pass

## rollback note
- if accuracy drops below target in production drills, restore prior card hierarchy and rerun guided operator calibration before rollout.

Now
- comprehension gate is green and above target.

Next
- finalize accessibility verification packet.

Blockers
- none.
