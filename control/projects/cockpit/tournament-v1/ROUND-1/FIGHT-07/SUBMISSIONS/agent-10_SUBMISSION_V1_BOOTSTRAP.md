# agent-10 Submission V1 Bootstrap (R16 F07)

## 1. Objective
- Deliver a deterministic and testable Round-1 submission frame for project Orbit (cockpit) that can absorb opponent ideas in Phase B without scope drift.

## 2. Scope in/out
- In:
  - Define a strict workflow for bootstrap -> absorption -> final.
  - Provide verifiable QA gates and a concrete DoD checklist.
  - Keep execution constrained to the allowed file paths.
- Out:
  - No repo-wide refactor.
  - No infra or deployment changes.
  - No speculative feature additions outside tournament constraints.

## 3. Architecture/workflow summary
- Step 1: Produce bootstrap with objective, scope, risks, QA, and DoD.
- Step 2: Validate opponent bootstrap availability at the exact expected path.
- Step 3: Run absorption pass in final (import >=3 ideas, reject >=1 weak own idea).
- Step 4: Re-run QA gates and verify DoD traceability.
- Step 5: Publish final with clear Now/Next/Blockers handoff.

## 4. Changelog vs previous version
- Initial bootstrap baseline for @agent-10 in R16/F07.
- Added deterministic phase split and blocker behavior.
- Added verifiable QA gates and explicit DoD controls.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- Accepted:
  - Deferred to Phase B after reading opponent bootstrap.
- Rejected:
  - None at bootstrap stage.
- Deferred:
  - All opponent-driven improvements until opponent file is available.

## 6. Risk register
- Risk: Opponent bootstrap missing.
  - Impact: Cannot execute absorption rules for final.
  - Mitigation: Hard stop and explicit blocker report with exact file path.
- Risk: Scope creep during final edits.
  - Impact: Non-deterministic output and lower reviewability.
  - Mitigation: Keep strict section template and in/out boundaries.
- Risk: Non-verifiable DoD.
  - Impact: Weak merge confidence.
  - Mitigation: Require concrete checks in QA gates and checklist.

## 7. Test and QA gates
- Gate 1: Bootstrap file exists.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-10_SUBMISSION_V1_BOOTSTRAP.md`
- Gate 2: Required 10 sections are present before final handoff.
  - Manual check against template headings.
- Gate 3: Opponent bootstrap existence check before Phase B.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_BOOTSTRAP.md`
- Gate 4: Final must include absorption constraints.
  - Verify `>=3 imported ideas` and `>=1 rejected weak own idea`.

## 8. DoD checklist
- [x] Objective is explicit and scoped.
- [x] Workflow is deterministic and phase-based.
- [x] Risks include mitigation.
- [x] QA gates are verifiable.
- [ ] Opponent ideas imported (Phase B).
- [ ] One weak own idea rejected with reason (Phase B).
- [ ] Final handoff complete with Now/Next/Blockers.

## 9. Next round strategy
- Prioritize high-signal opponent ideas that improve determinism, testability, and rollback clarity.
- Reject any own idea that adds complexity without measurable QA gain.
- Keep final minimal, explicit, and reversible.

## 10. Now/Next/Blockers
- Now:
  - Bootstrap created with required format and QA gates.
- Next:
  - Check opponent bootstrap file.
  - If present, run absorption pass and write final.
- Blockers:
  - Pending opponent bootstrap presence check.
