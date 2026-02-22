# ISSUE-CP-0002 - Policy engine curated fail-open

- Owner: victor -> @agent-2
- Phase: Ship
- Status: Done

## Objective
- Enforce curated-only policy with fail-open behavior and explicit warning logs.

## Scope (In)
- Curated allowlist validation.
- Fail-open mode when policy source is unavailable.
- Structured warning events.

## Scope (Out)
- UI notification details.
- Role pack defaults.

## Now
- Done.

## Next
- None.

## Blockers
- None.

## Done (Definition)
- [x] Non-curated skills are blocked in normal mode.
- [x] Fail-open path does not crash flow and emits warning.
- [x] Policy behavior covered by tests (9/9 pass).

## Proof
- Module: `app/services/skills_policy.py`
- Tests: `tests/verify_skills_policy.py` (9 passed, 0 failed)
- Regression: `tests/verify_execution_router.py` passes

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md

## Risks
- Over-blocking valid skills due to parser edge cases.
