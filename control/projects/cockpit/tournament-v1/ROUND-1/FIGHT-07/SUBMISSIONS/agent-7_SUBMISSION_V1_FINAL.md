# agent-7 Submission V1 Final (R16 F07)

## 1. Objective
- Deliver a deterministic, implementation-ready, and testable final submission for cockpit R16/F07 that fully complies with absorption and DoD constraints.

## 2. Scope in/out
- In:
  - Keep strict bootstrap -> check -> absorption -> QA -> handoff workflow.
  - Import opponent ideas that improve determinism and verification signal.
  - Keep all gates and checklist items verifiable.
- Out:
  - No repo-wide refactor.
  - No infra/deployment work.
  - No feature expansion outside tournament constraints.

## 3. Architecture/workflow summary
- Step 1: Confirm opponent bootstrap exists at exact required path.
- Step 2: Load baseline from bootstrap and preserve required 10-section contract.
- Step 3: Absorb opponent ideas into workflow, QA, and risk controls.
- Step 4: Reject weak own idea(s) that reduce verification quality.
- Step 5: Run command-based QA gates plus short manual semantic review.
- Step 6: Publish final with clear Now/Next/Blockers handoff.

## 4. Changelog vs previous version
- Imported four opponent ideas from @agent-10 into the final control model.
- Added explicit hard-stop blocker behavior tied to exact file path checks.
- Upgraded QA from manual-only section check to semi-automated heading count plus quick manual review.
- Completed final-phase DoD items and handoff status.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- Accepted:
  - Deterministic phase pipeline with explicit step ordering.
  - Hard-stop blocker policy with exact missing-file path reporting.
  - QA gates mapped directly to DoD traceability.
  - Scope-creep guardrails via strict in/out boundaries and fixed section structure.
- Rejected:
  - Weak own idea rejected: manual-only section presence check.
  - Reason: too fragile and not reliably repeatable across reviewers.
  - Replacement: semi-automated section counting plus quick human semantic check.
- Deferred:
  - No additional opponent ideas deferred in this round.

## 6. Risk register
- Risk: Opponent file state changes after precheck.
  - Impact: Absorption evidence can become stale.
  - Mitigation: Re-run exact path check before handoff.
- Risk: Heading-count check passes while section content quality is weak.
  - Impact: False confidence in completion.
  - Mitigation: Combine command checks with a short semantic review pass.
- Risk: Late edits reintroduce scope creep.
  - Impact: Lower determinism and harder merge review.
  - Mitigation: Freeze section order and keep strict in/out boundaries.

## 7. Test and QA gates
- Gate 1: Required files exist.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_BOOTSTRAP.md`
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-10_SUBMISSION_V1_BOOTSTRAP.md`
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_FINAL.md`
- Gate 2: Final has exactly 10 numbered sections.
  - `test "$(rg -n '^## [0-9]+\\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_FINAL.md | wc -l | tr -d ' ')" = "10"`
- Gate 3: Final includes required ending status block.
  - `rg -n '^## 10\\. Now/Next/Blockers$' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-07/SUBMISSIONS/agent-7_SUBMISSION_V1_FINAL.md`
- Gate 4: Absorption constraints are satisfied.
  - Manual verification: `>=3 imported opponent ideas` and `>=1 rejected weak own idea` in Section 5.

## 8. DoD checklist
- [x] Output has 10 required sections in required order.
- [x] Final imports at least 3 opponent ideas.
- [x] Final rejects at least 1 weak own idea with explicit reason.
- [x] QA gates are executable and traceable to completion checks.
- [x] Risks are documented with mitigations.
- [x] Final ends with actionable Now/Next/Blockers.

## 9. Next round strategy
- Keep deterministic baseline and only add complexity with measurable QA benefit.
- Maintain acceptance/rejection/defer discipline for opponent idea absorption.
- Add rollback note for any future increase in process complexity.

## 10. Now/Next/Blockers
- Now:
  - Final submission published with absorption constraints satisfied and DoD complete.
- Next:
  - Wait for tournament update packet.
  - Prepare delta-only upgrades for next round prompt.
- Blockers:
  - None.
