# agent-10 Submission V2 Final (QF F12)

## 1. Objective
- Deliver a deterministic, testable, and high-scoring QF final for project Orbit with final-only discipline, stronger risk control, and measurable feasibility evidence.

## 2. Scope in/out
- In:
  - Use only two allowed inputs: self R1 final and opponent R1 final.
  - Apply a locked import map from opponent ideas with explicit IDs.
  - Keep all validation command-based and reproducible.
  - Preserve strict project scope: stabilization-first slices (UI + docs + setup + MCP).
- Out:
  - No legacy-phase artifact dependency.
  - No repo-wide refactor or architecture jump.
  - No speculative feature additions outside QF fight scope.

## 3. Architecture/workflow summary
- Step 1: Verify both required R1 final inputs are present at exact paths.
- Step 2: Build and apply opponent import map (`O15-A1..O15-A4`) with acceptance decisions.
- Step 3: Apply one explicit weak-own-idea rejection (`SELF-R1`) to improve feasibility.
- Step 4: Run full command-based validation on the V2 final output path.
- Step 5: Publish handoff with `Now/Next/Blockers` and evidence-first scoring posture.

## 4. Changelog vs previous version
- Upgraded from R1 to L2 by adding a locked opponent import map with explicit IDs (`O15-A1..O15-A4`).
- Improved auditability with path-specific command gates for structure, absorption, footer contract, and ASCII contract.
- Added explicit tie-break protection: risk and feasibility evidence are prioritized first.
- Rejected weak own idea `SELF-R1` to remove legacy dependency and improve final-only compliance.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- Accepted:
  - `O15-A1`: owner-unique issue -> PR -> test -> review -> ship flow.
  - `O15-A2`: explicit conformance behavior when a required external input is missing.
  - `O15-A3`: concrete QA gates for ASCII contract, required sections, and footer contract.
  - `O15-A4`: stabilization-first scope framing (UI + docs + setup + MCP slices) as execution framing, not architecture expansion.
- Rejected:
  - `SELF-R1`: legacy pre-final artifact dependent validation flow.
  - Reason: lowers feasibility in final-only dispatch and weakens audit clarity.
- Deferred:
  - Any broader control-plane or replay architecture expansion beyond QF deliverable scope.

## 6. Risk register
- Risk: required input file missing at execution time.
  - Impact: submission becomes non-compliant and non-verifiable.
  - Mitigation: hard-stop preflight with exact-path blocker message.
- Risk: scope creep from over-integration.
  - Impact: lower feasibility and timeline risk.
  - Mitigation: keep only locked imports (`O15-A1..O15-A4`) and reject non-essential expansion.
- Risk: weak evidence quality in scoring review.
  - Impact: tie-break disadvantage on risk and feasibility.
  - Mitigation: keep command-based checks with explicit expected outputs.
- Risk: contract drift from required output format.
  - Impact: formal rejection risk.
  - Mitigation: enforce exact 10-section contract and `Now/Next/Blockers` footer.

## 7. Test and QA gates
- Gate 1: V2 final file exists.
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md`
- Gate 2: V2 final has exactly 10 numbered sections.
  - `rg -n '^## [0-9]+\\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md | wc -l`
  - Expected: `10`
- Gate 3: absorption IDs are present and verifiable.
  - `rg -n 'O15-A1|O15-A2|O15-A3|O15-A4|SELF-R1' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md`
  - Expected: at least 3 opponent IDs (`O15-A*`) and one self rejection ID (`SELF-R1`).
- Gate 4: footer contract is present.
  - `tail -n 12 /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md`
  - Expected: includes `Now`, `Next`, `Blockers`.
- Gate 5: ASCII-only contract.
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md`
  - Expected: no output.
- Gate 6: final-only language guard.
  - `rg -n 'legacy-phase artifact dependency|final-only' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-12/SUBMISSIONS/agent-10_SUBMISSION_V2_FINAL.md`
  - Expected: references to final-only discipline are explicit.

## 8. DoD checklist
- [x] Objective is explicit and scoring-oriented for QF.
- [x] Scope boundaries are explicit and enforceable.
- [x] Architecture/workflow is deterministic with 5 ordered steps.
- [x] Opponent absorption rule satisfied with >=3 accepted opponent ideas.
- [x] One weak own idea rejected with explicit reason (`SELF-R1`).
- [x] Risk register includes hard-stop and anti-scope-creep controls.
- [x] QA gates are command-based with expected outcomes.
- [x] Output stays ASCII-only.
- [x] Output uses exactly the 10 required sections.
- [x] Final handoff ends with `Now/Next/Blockers`.

## 9. Next round strategy
- Keep risk-first and feasibility-first evidence so tie-breaks remain favorable.
- Preserve command-based verification as default and avoid narrative-only claims.
- Import only high-leverage opponent ideas with explicit IDs and bounded scope.
- Maintain stabilization-first delivery slices before any architecture expansion.

## 10. Now/Next/Blockers
- Now:
  - QF V2 final is structured for deterministic scoring with locked absorption and verifiable gates.
- Next:
  - Run all QA commands and hand off with evidence lines for judge review.
  - Reuse this L2 evidence model in the next fight with strict scope control.
- Blockers:
  - None.
