# 08_VULGARISATION_SPEC

## Context
Even in a stability-first variant, operators need clear explanations under pressure. This spec defines a vulgarisation layer that translates persistence internals into fast decisions.

## Problem statement
Operators cannot act quickly if failure signals are technical but not decision-oriented. We need a concise UI contract for "what happened, what is blocked, what is safe next".

## Proposed design
### Tab goal
Provide a "Persistence Health" panel with plain language summaries, confidence level, and immediate next actions.

### Display blocks
- Current run health
- Replay determinism status
- Corruption detection status
- Approval gate status
- Recommended next action

### 60-second comprehension target
An operator should answer in 60 seconds:
- Is data safe?
- Can we continue?
- Do we rollback?
- Do we need @clems approval now?

### Content contract
Each incident card includes:
- What changed
- Why it matters
- What to do now
- Confidence level
- Link to evidence run id

## Interfaces and contracts
UI payload contract:
- `project_id`
- `run_id`
- `health_state`
- `determinism_state`
- `corruption_state`
- `approval_state`
- `recommended_action`
- `evidence_links[]`
- `updated_at`

Severity map:
- green: continue
- amber: continue with guard
- red: rollback and escalate

## Failure modes
- FM1: stale status shown during incident.
  - Mitigation: freshness TTL and stale badge.
- FM2: contradictory recommendations.
  - Mitigation: one decision engine source with explicit precedence.
- FM3: overload from too many metrics.
  - Mitigation: collapse to top decision signals and expandable details.

## Validation strategy
- Operator drills with timed comprehension test.
- A/B test on action accuracy and response time.
- Incident retrospective scoring on signal clarity.

## Rollout/rollback
- Rollout in read-only advisory mode.
- Enable action links after operator confidence threshold.
- Rollback to minimal status panel if confusion score rises.

## Risks and mitigations
- Risk: oversimplification hides nuance.
  - Mitigation: progressive disclosure with evidence links.
- Risk: alert fatigue.
  - Mitigation: severity routing and suppression windows.

## Resource impact
- Frontend effort: low-medium.
- Backend payload adapters: medium.
- Operator training: low.

Evidence tags used: [P6][P7][R2][R3][S1][S2].
