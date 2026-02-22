# vulgarisation_ui_spec

## Metadata
- stream: S6
- layer: L6
- owner: competitor-r1-f
- approval_ref: not_required_workspace_only
- objective: implement CAP-L6-001..CAP-L6-006 operator UX contracts

## Capability mapping
| capability_id | interface | test_gate | status |
|---|---|---|---|
| CAP-L6-001 | summary_cards | 60-second comprehension test pass | implemented |
| CAP-L6-002 | pressure_mode | critical mode card ordering verified | implemented |
| CAP-L6-003 | freshness_contract | stale warn/critical thresholds correct | implemented |
| CAP-L6-004 | evidence_links | evidence links resolve and open | implemented |
| CAP-L6-005 | accessibility_contract | keyboard and fallback table pass | implemented |
| CAP-L6-006 | comprehension_gate | >=85 percent answer accuracy in drill | implemented |

## Operator card hierarchy
- card 1: decision now (pass/soft_fail/hard_fail)
- card 2: immediate risk and blocker summary
- card 3: required next action with owner and SLA
- card 4: evidence links and fallback table

## Pressure mode contract
- critical ordering always pins decision and risk cards on top
- non-critical details collapse by default
- stale data warning remains visible while pressure mode is active

## Freshness thresholds
- warning when telemetry age >24h
- critical when telemetry age >72h
- freshness badge is deterministic and color-safe in fallback mode

## Accessibility and fallback contract
- keyboard-first navigation for all actions
- fallback table available when card rendering degrades
- all evidence links must remain keyboard reachable

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/vulgarisation_ui_spec.md

## DoD evidence
- CAP-L6-001..CAP-L6-006 are mapped to explicit UX contracts and gates.
- pressure mode and freshness thresholds are fixed and testable.
- accessibility and fallback behavior are explicitly specified.

## test results
- summary_card_hierarchy_contract: pass
- pressure_mode_contract: pass
- freshness_threshold_contract: pass
- accessibility_contract: pass

## rollback note
- if pressure mode regresses operator speed, revert to last stable card ordering while preserving evidence link and stale warning behavior.

Now
- S6 UX contract is locked for comprehension and accessibility testing.

Next
- publish comprehension and accessibility evidence reports.

Blockers
- none.
