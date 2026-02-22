# 08 - Vulgarisation Spec (Operator clarity under pressure)

## Context
Operators need to understand release risk quickly. Eval harness output must be actionable in under 60 seconds, not buried in dense logs.

## Problem statement
Technical evidence is often accurate but unreadable during incidents. This slows decisions and increases unsafe overrides.

## Proposed design
Define a `Vulgarisation` panel in Cockpit with 4 cards:
1. `Release Verdict`: PASS / SOFT_FAIL / HARD_FAIL.
2. `Why`: top 3 blocking reasons in plain language.
3. `What changed`: benchmark and risk deltas since previous run.
4. `What to do now`: owner + next action + ETA.

Design rules:
- first line must answer: "Can we release now?"
- max 12 lines before fold,
- severity color coding with text fallback,
- every claim maps to evidence artifact link.

## Interfaces and contracts
UI contract (`vulgarisation_payload.json`):
- `run_id`
- `verdict`
- `confidence_score`
- `top_reasons[]`
- `recommended_actions[]`
- `owner_mentions[]`
- `evidence_links[]`

Language contract:
- short verbs,
- no unexplained jargon,
- include owner handles: `@clems`, `@victor`, `@leo` when decision authority is needed.

## Failure modes
- Over-simplification hides critical nuance.
- Inconsistent wording across runs confuses operators.
- Missing evidence links breaks trust.

## Validation strategy
- 60-second comprehension test:
  - 10 operators,
  - answer 3 questions in <= 60 seconds,
  - pass threshold >= 90 percent correct.
- A/B test summary templates for ambiguity rate.
- Incident drill with timed decision quality scoring.

## Rollout/rollback
- Rollout:
  - shadow render from existing gate outputs,
  - human review loop for wording,
  - hard requirement in release packet.
- Rollback:
  - fallback to previous template version,
  - keep raw evidence links untouched.

## Risks and mitigations
- Risk: pretty UI without decision value.
  - Mitigation: enforce action card + owner + ETA.
- Risk: stale text templates.
  - Mitigation: monthly content review with incident examples.
- Risk: authority confusion.
  - Mitigation: explicit owner mapping tied to gate type.

## Resource impact
- Moderate frontend/design effort (~2 sprints).
- High operator ROI via faster incident and release decisions.
- Minimal runtime overhead since payload is derived from existing verdict artifacts.

## References
Key sources: [P3][P4][R1][R5][S3], assumptions [A1][A3].
