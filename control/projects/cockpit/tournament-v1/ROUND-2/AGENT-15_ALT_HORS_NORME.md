# Round 2 - Agent-15 Alternative Hors Norme

## Context
- Lane: CDX
- Objective: propose a high-leverage non-standard option with kill-switch.

## Outlier Proposal
- Introduce a "Workflow Control Plane" layer as a single event log contract before any UI refresh.
- All status changes, dispatch actions, blockers, and decisions append to one normalized event stream.
- UI reads derived state from this stream, not from scattered files.

## Potential Leverage
- Single timeline for audit and debugging.
- Deterministic rebuild of project state.
- Easier simulation and replay of failure scenarios.

## Major Risks
- Architecture jump may exceed V1 scope.
- Initial migration complexity is high.
- Could delay immediate workflow fixes.

## Kill-Switch
- Abort outlier adoption if any of these trigger:
1. estimated effort > 2 implementation lots,
2. no incremental deployment path,
3. cannot preserve current file contracts.

## Minimal Test Pilot
- Pilot only one event type: agent status transition.
- Compare consistency against current state model for 48h.
- Stop if mismatch rate > 5 percent.

## DoD For Accepting Outlier
- pilot results documented,
- mismatch rate <= 5 percent,
- incremental rollout path validated,
- no regression in operator 60-second readability.

## Actionability
- Actionable ratio: 4/6 (67 percent).
- Recommendation: keep as deferred experiment unless pilot is trivial.
