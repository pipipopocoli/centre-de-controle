# agent-5 Submission V1 Bootstrap (R16 F03)

You are: @agent-5
PROJECT LOCK: cockpit
Round: R16
Fight: F03
Complexity level required: L1
Project codename now: Titan
Opponent: @agent-12

## 1. Objective
- Build an implementation-ready L1 bootstrap for Titan with clear ownership, deterministic flow, and shell-verifiable quality gates.
- Keep execution small, auditable, and ready for absorption in Phase B.

## 2. Scope in/out
In:
- One-task one-owner execution language with explicit DoD evidence.
- Deterministic closure using `Now/Next/Blockers`.
- Risk and QA controls that are command-verifiable.

Out:
- Product feature coding, runtime API changes, or schema work.
- Cross-project process expansion outside `cockpit`.
- L2/L3 complexity experiments.

## 3. Architecture/workflow summary
- Step 1: Validate required write path and section contract.
- Step 2: Publish bootstrap with strict 10-section structure.
- Step 3: Hold Phase B until opponent bootstrap exists.
- Step 4: Mark one weak self idea for mandatory rejection in FINAL.
- Step 5: Gate completion with executable shell checks only.

## 4. Changelog vs previous version
- Initial bootstrap baseline created for @agent-5 in R16 F03.
- Added deterministic phase split: bootstrap first, absorption second.
- Added weak self marker `SELF-W1` to enforce explicit rejection in FINAL.

## 5. Imported opponent ideas (accepted/rejected/deferred)
Accepted:
- `SELF-W1` (self): manual-only QA review before done.
- Reason: acceptable as bootstrap placeholder only.

Rejected:
- None in bootstrap.

Deferred:
- `IDEA-O01`: phase-gate strictness from opponent file, decide in FINAL.
- `IDEA-O02`: command-based gate style from opponent file, decide in FINAL.
- `IDEA-O03`: blocker-path explicit reporting pattern, decide in FINAL.

## 6. Risk register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|---|---|---:|---:|---:|---|
| R1 | Opponent bootstrap missing blocks absorption | 4 | 5 | 20 | Hard stop and explicit blocker path in section 10 |
| R2 | Manual QA could mark false done state | 3 | 4 | 12 | Replace `SELF-W1` with command gates in FINAL |
| R3 | Section drift breaks template compliance | 2 | 4 | 8 | Lock exact numbering and naming |
| R4 | Ownership ambiguity slows delivery | 2 | 5 | 10 | Keep one-owner language in workflow and DoD |
| R5 | Status closure becomes vague | 3 | 3 | 9 | Enforce explicit `Now/Next/Blockers` lines |

## 7. Test and QA gates
- Gate B1: exactly 10 numbered sections.
  - `test "$(rg -n '^## [0-9]+\\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-03/SUBMISSIONS/agent-5_SUBMISSION_V1_BOOTSTRAP.md | wc -l | tr -d ' ')" = "10"`
  - Pass criteria: value equals 10.
- Gate B2: status markers are present.
  - `rg -n '^Now:|^Next:|^Blockers:' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-03/SUBMISSIONS/agent-5_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: all 3 markers found.
- Gate B3: ASCII-only output.
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-03/SUBMISSIONS/agent-5_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: no output.
- Gate B4: bootstrap file is non-empty.
  - `test -s /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-03/SUBMISSIONS/agent-5_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: command exits 0.

## 8. DoD checklist
- [x] Exactly 10 required sections are present.
- [x] Scope is explicit and bounded.
- [x] Workflow is deterministic and phase-gated.
- [x] Risk register is quantified with mitigations.
- [x] QA gates are command-verifiable.
- [x] Weak self idea is explicitly marked for FINAL rejection.
- [x] Output is ASCII-only.

## 9. Next round strategy
- Read opponent bootstrap from required path.
- Import at least 3 opponent ideas with `OPP-A*` accepted markers.
- Reject `SELF-W1` with reason and deterministic replacement.
- Keep final output short, testable, and L1-compliant.

## 10. Now/Next/Blockers
Now:
- Bootstrap published with exact 10-section contract and verifiable gates.

Next:
- Run Phase B absorption and publish FINAL for F03.

Blockers:
- None. Opponent bootstrap is available at required path.
