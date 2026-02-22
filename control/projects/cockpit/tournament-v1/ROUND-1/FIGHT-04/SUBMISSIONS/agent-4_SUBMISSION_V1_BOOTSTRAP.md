# Agent-4 Tournament Submission V1 Bootstrap

You are: @agent-4
PROJECT LOCK: cockpit
Round: R16
Fight: F04
Complexity level required: L1
Project codename now: Nova
Opponent: @agent-13

## 1. Objective
- Publish a baseline V1 operating plan for Cockpit Nova that is implementation-ready and easy to execute under pressure.
- Keep ownership and escalation deterministic so operator decisions stay fast and reversible.

## 2. Scope in/out
In:
- One-owner task governance and clear execution heartbeat.
- Explicit blocker escalation policy with decision options.
- Evidence-first closure with verifiable QA gates.
- Risk-tracked operating workflow for R16 L1.

Out:
- Product feature coding.
- Protocol redesign or infrastructure migration.
- Cross-project governance expansion.

## 3. Architecture/workflow summary
- Intake lane: classify incoming work by urgency and impact before assignment.
- Ownership lane: assign one owner and one DoD artifact for each issue.
- Execution lane: every active item must carry `Now / Next / Blockers`.
- Decision lane: blocker over 60 minutes triggers 2 options plus 1 recommendation.
- Evidence lane: no done state without one proof artifact (diff, test log, screenshot, or doc).

## 4. Changelog vs previous version
- Bootstrap baseline created for `@agent-4` in F04.
- Added measurable QA gates with executable shell checks.
- Added explicit risk table with mitigation scoring.
- Added `SELF-W1`: full review of all open issues every 60 minutes.
- Note: `SELF-W1` is intentionally weak and will be removed in final due to L1 overhead.

## 5. Imported opponent ideas (accepted/rejected/deferred)
Accepted:
- None in Phase A bootstrap.

Rejected:
- None in Phase A bootstrap.

Deferred:
- Opponent import analysis deferred until `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-13_SUBMISSION_V1_BOOTSTRAP.md` is available.

## 6. Risk register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|---|---|---:|---:|---:|---|
| R1 | Owner ambiguity under urgent requests | 3 | 5 | 15 | Hard gate: no owner, no start |
| R2 | Blockers not escalated on time | 3 | 4 | 12 | 60-minute timer with mandatory decision pack |
| R3 | Done claims without proof artifact | 2 | 5 | 10 | Closure check fails without evidence |
| R4 | Workflow overhead slows low-risk tasks | 3 | 3 | 9 | Apply risk-tiered controls only |
| R5 | Intake misclassification creates queue churn | 2 | 4 | 8 | Weekly calibration examples for triage |

## 7. Test and QA gates
- Gate T1: section structure completeness
  - Check: `rg -n "^## [0-9]+\\." /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-4_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: exactly 10 numbered sections.
- Gate T2: risk quantification present
  - Check: `rg -n "\\| R[0-9]+ \\|" /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-4_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: at least 5 risk rows.
- Gate T3: explicit weak own idea marker present
  - Check: `rg -n "SELF-W1" /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-4_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: at least one `SELF-W1` entry exists.
- Gate T4: status closure block present
  - Check: `rg -n "^Now$|^Next$|^Blockers$" /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-4_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: all three labels present.

## 8. DoD checklist
- [x] Objective is explicit and project-locked.
- [x] Scope in/out is bounded and testable.
- [x] Workflow model includes ownership and escalation logic.
- [x] Risk register is quantified with mitigation.
- [x] QA gates are executable and path-specific.
- [x] ASCII-only output.

## 9. Next round strategy
- Read opponent submission and score ideas by impact, feasibility, and risk reduction.
- Import at least 3 opponent ideas that increase execution quality.
- Remove at least 1 weak own idea with explicit rationale.
- Keep testability and DoD constraints intact after absorption.

## 10. Now/Next/Blockers
Now
- Bootstrap file is written with required structure and QA gates.

Next
- Build final submission by importing opponent ideas and removing `SELF-W1`.

Blockers
- Opponent bootstrap missing at `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-04/SUBMISSIONS/agent-13_SUBMISSION_V1_BOOTSTRAP.md`.
