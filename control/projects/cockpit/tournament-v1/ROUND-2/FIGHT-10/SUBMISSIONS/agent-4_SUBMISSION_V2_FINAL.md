# Agent-4 Tournament Submission V2 Final

You are: @agent-4
PROJECT LOCK: cockpit
Round: QF
Fight: F10
Complexity level required: L2
Project codename now: Nova
Opponent: @agent-12

## 1. Objective
- Deliver a stronger L2 final that beats @agent-12 on impact while preserving deterministic execution quality.
- Increase operator throughput with risk-tiered handoff controls and threshold-based QA gates.

## 2. Scope in/out
In:
- Final-only operating plan upgrade from V1 to L2 for QF F10.
- Deterministic workflow with explicit phase gates and owner accountability.
- Absorption of high-value opponent ideas with testable evidence.
- Quantified risk handling and strict verifiable DoD.

Out:
- Runtime feature implementation or API changes.
- Cross-project governance changes outside cockpit.
- Bootstrap artifacts for QF.

## 3. Architecture/workflow summary
- Step 1: Preflight input lock and fail-fast blocker path checks.
- Step 2: Intake split into `fast_lane` and `deep_lane`, then assign risk tier (`high`, `medium`, `low`).
- Step 3: One-owner assignment with one required evidence artifact per issue.
- Step 4: Handoff SLA is tiered by risk: `high=10m`, `medium=30m`, `low=60m`.
- Step 5: Execution follows deterministic phase gates: Plan -> Implement -> Test -> Review -> Ship.
- Step 6: Blocker over 60 minutes triggers 2 options plus 1 recommended decision.
- Step 7: End-of-day unresolved blocker digest keeps next-day triage deterministic.

## 4. Changelog vs previous version
- Upgraded from V1 L1 to QF L2 final-only submission with stricter phase control.
- Imported 4 opponent ideas that improve gate precision and workflow determinism.
- Rejected weak own idea `SELF-W1` (fixed 15-minute SLA for all handoffs).
- Replaced `SELF-W1` with risk-tiered SLA thresholds to reduce deep-lane overhead.
- Added threshold QA checks for section count, absorption counts, and self-reject compliance.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- OPP-A01 | source: opponent | decision: accepted | reason: absorb deterministic phase-flow wording to reduce execution ambiguity | test: section 3 keeps explicit ordered steps.
- OPP-A02 | source: opponent | decision: accepted | reason: absorb strict section-lock discipline to prevent template drift | test: Gate Q2 enforces exactly 10 sections.
- OPP-A03 | source: opponent | decision: accepted | reason: absorb explicit absorption mapping format (`source|decision|reason|test`) for judge traceability | test: section 5 uses normalized mapping lines.
- OPP-A04 | source: opponent | decision: accepted | reason: absorb threshold gate style (`test ... =`, `>=`) to avoid false done states | test: Gates Q2-Q5 are numeric threshold checks.
- OPP-R01 | source: opponent | decision: rejected | reason: keep ownership singular and avoid shared ownership drift in urgent work | test: section 3 keeps one-owner lane as hard rule.
- SELF-W1 | source: self | decision: rejected | reason: fixed 15-minute SLA for all handoffs is too rigid at L2 and adds noise on deep-lane tasks | test: section 3 now uses risk-tiered SLA thresholds.
- OPP-D01 | source: opponent | decision: deferred | reason: naming-style refinements are low impact for QF scoring window | test: revisit in SF only if scoring delta is positive.

## 6. Risk register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|---|---|---:|---:|---:|---|
| R1 | Wrong risk-tier assignment at intake | 3 | 4 | 12 | Add tier examples and weekly calibration review |
| R2 | Tiered SLA not applied consistently | 3 | 5 | 15 | Auto-check missed SLA events in daily digest |
| R3 | Owner ambiguity returns during incidents | 2 | 5 | 10 | Hard gate: no owner, no execution |
| R4 | QA gate fatigue slows delivery | 2 | 4 | 8 | Keep threshold gates short and script-friendly |
| R5 | Absorption mapping becomes cosmetic | 2 | 4 | 8 | Require reason plus test field on every mapping line |

## 7. Test and QA gates
- Gate Q1: final file exists and is non-empty.
  - `test -s /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md`
  - Pass criteria: command exits 0.
- Gate Q2: exactly 10 numbered sections.
  - `test "$(rg -n '^## [0-9]+\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" = "10"`
  - Pass criteria: value equals 10.
- Gate Q3: accepted opponent imports >= 3.
  - `test "$(rg -n 'source: opponent \| decision: accepted' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 3`
  - Pass criteria: value is >= 3.
- Gate Q4: weak own reject >= 1.
  - `test "$(rg -n 'source: self \| decision: rejected' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 1`
  - Pass criteria: value is >= 1.
- Gate Q5: quantified risk rows >= 5.
  - `test "$(rg -n '\| R[0-9]+ \|' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 5`
  - Pass criteria: value is >= 5.
- Gate Q6: section 10 and closure markers present.
  - `rg -n '^## 10\. Now/Next/Blockers$|^Now$|^Next$|^Blockers$' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md`
  - Pass criteria: section header and all 3 markers are present.
- Gate Q7: ASCII strict.
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md`
  - Pass criteria: no output.
- Gate Q8: complexity header locked to L2.
  - `rg -n '^Complexity level required: L2$' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-4_SUBMISSION_V2_FINAL.md`
  - Pass criteria: exactly one matching line.

## 8. DoD checklist
- [x] Final-only output path is respected.
- [x] Metadata header is complete and fight-locked.
- [x] Exactly 10 required sections are present.
- [x] At least 3 opponent ideas are accepted with reasons and tests.
- [x] At least 1 weak own idea is rejected with reason and replacement.
- [x] Risk register has >=5 quantified rows.
- [x] QA gates are executable and threshold-based.
- [x] Output is ASCII-only and ends with Now/Next/Blockers.

## 9. Next round strategy
- Keep only imports that show measurable scoring lift in feasibility and risk.
- Promote tiered SLA and phase-gate checks as reusable SF baseline.
- Remove any gate that does not improve signal-to-noise after QF review.
- Enter SF with delta-only upgrades to keep delivery small and reversible.

## 10. Now/Next/Blockers
Now
- QF V2 final is written with L2 controls, opponent absorption, and strict verifiable gates.

Next
- Wait for @agent-12 V2 final, then run judge scoring and capture top deltas for SF.

Blockers
- None.
