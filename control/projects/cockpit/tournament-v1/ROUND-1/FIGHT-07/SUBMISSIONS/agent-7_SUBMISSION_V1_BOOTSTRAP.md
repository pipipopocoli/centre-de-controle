# agent-7 Submission V1 Bootstrap (R16 F07)

## 1. Objective
- Deliver a deterministic and testable submission frame for cockpit R16/F07 (Cipher) with clean Phase B handoff.

## 2. Scope in/out
- In:
  - Define bootstrap -> opponent check -> absorption -> QA -> final handoff workflow.
  - Define verifiable QA gates and a concrete DoD checklist.
  - Stay inside allowed read/write paths.
- Out:
  - No repo-wide refactor.
  - No infra or deployment changes.
  - No speculative feature additions outside tournament constraints.

## 3. Architecture/workflow summary
- Step 1: Write bootstrap with all required sections.
- Step 2: Verify opponent bootstrap path exactly.
- Step 3: If present, run final absorption pass (>=3 imported opponent ideas, >=1 rejected weak own idea).
- Step 4: Run QA gates and verify DoD traceability.
- Step 5: Publish final with clear Now/Next/Blockers.

## 4. Changelog vs previous version
- Initial bootstrap baseline for @agent-7 in R16/F07.
- Added deterministic phase split and explicit hard-stop behavior.
- Added verifiable QA gates and DoD controls.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- Accepted:
  - Deferred to Phase B after opponent bootstrap read.
- Rejected:
  - None at bootstrap stage.
- Deferred:
  - All opponent-driven improvements until Phase B.

## 6. Risk register
- Risk: Opponent bootstrap missing.
  - Impact: Final absorption cannot start.
  - Mitigation: Hard stop with exact blocker file path.
- Risk: Scope creep during final edits.
  - Impact: Non-deterministic output and weaker reviewability.
  - Mitigation: Keep strict section order and scope boundaries.
- Risk: Weak verification quality.
  - Impact: False done state.
  - Mitigation: Keep command-based checks plus explicit DoD checklist.

## 7. Test and QA gates
- Gate 1: Bootstrap file exists.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_BOOTSTRAP.md`
- Gate 2: Opponent bootstrap exists before Phase B.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-10_SUBMISSION_V1_BOOTSTRAP.md`
- Gate 3: Final has exactly 10 numbered sections.
  - `rg -n '^## [0-9]+\\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_FINAL.md`
- Gate 4: Final contains absorption constraints.
  - Verify `>=3 imported opponent ideas` and `>=1 rejected weak own idea`.
- Gate 5: Final ends with `Now/Next/Blockers`.

## 8. DoD checklist
- [x] Objective is explicit and scoped.
- [x] Deterministic workflow is documented.
- [x] Risks include mitigations.
- [x] QA gates are verifiable.
- [ ] Opponent ideas imported in final (Phase B).
- [ ] One weak own idea rejected with reason (Phase B).
- [ ] Final handoff complete with Now/Next/Blockers.

## 9. Next round strategy
- Prioritize high-signal ideas that improve determinism, QA signal, and rollback clarity.
- Reject ideas that add complexity without measurable verification gain.
- Keep output concise, explicit, and reversible.

## 10. Now/Next/Blockers
- Now:
  - Bootstrap published with deterministic workflow, QA gates, and DoD baseline.
- Next:
  - Verify opponent bootstrap file.
  - Run absorption pass and publish final.
- Blockers:
  - None if opponent bootstrap exists; hard stop otherwise.
