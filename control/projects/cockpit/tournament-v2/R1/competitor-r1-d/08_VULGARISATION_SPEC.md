# 08_VULGARISATION_SPEC - Operator clarity under pressure

## Context
Even with strong memory internals, operators need simple, high-signal explanations to trust actions and gate decisions.

## Problem statement
Complex memory status without clear language causes wrong interventions, delayed decisions, and gate errors.

## Proposed design
### 60-second comprehension model
- In 60 seconds, operator must answer:
  1. Is project memory healthy?
  2. Is retrieval trustworthy for this action?
  3. Is promotion pending and who must approve?
  4. Is there a rollback-safe path right now?

### UI contract (memory vulgarisation tab)
- Block A: Health summary
  - status: green/yellow/red
  - top issue and owner
- Block B: Retrieval confidence
  - lexical/hybrid mode
  - confidence tag and freshness window
- Block C: Isolation status
  - contamination incidents (should be zero)
  - cross-project block count
- Block D: Promotion queue
  - pending items count
  - approver required (@clems)
- Block E: Action panel
  - safe next action
  - rollback entry point

### Microcopy standards
- No internal jargon in primary labels.
- Every warning must include action and owner.
- Use "ASSUMPTION" tag when data is uncertain.

## Interfaces and contracts
- MemoryStatusViewModel
  - project_id
  - health_state
  - confidence_state
  - isolation_state
  - promotion_state
  - recommended_action
- ComprehensionTestResult
  - tester_role
  - elapsed_seconds
  - correct_answers
  - confusion_points

## Failure modes
- FM-VUL-1: green status with hidden critical degradation.
- FM-VUL-2: warning without owner/action.
- FM-VUL-3: stale metrics shown as real-time.

## Validation strategy
- 60-second comprehension test with operators.
- Scenario drills: normal/degraded/recovery.
- Linguistic QA for ambiguous terms.

## Rollout/rollback
- Rollout
  - shadow display mode first.
  - enforce primary display after comprehension pass rate threshold.
- Rollback
  - revert to minimal status mode if confusion rate increases.

## Risks and mitigations
- Risk: oversimplification hides important details.
  - Mitigation: expandable detail panel with provenance links.
- Risk: too much detail breaks 60-second target.
  - Mitigation: strict primary card budget and progressive disclosure.

## Resource impact
- UX lane needs 2 dev + 1 product writer + 1 QA reviewer.
- Ongoing cost: monthly copy audit and scenario refresh.

## Evidence tags used
[P4][P6][R6][S3][ASSUMPTION-A12]
