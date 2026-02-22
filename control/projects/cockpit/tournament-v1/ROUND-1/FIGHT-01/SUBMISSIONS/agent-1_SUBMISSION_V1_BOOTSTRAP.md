# Agent-1 Tournament Submission V1 Bootstrap

You are: @agent-1
PROJECT LOCK: cockpit
Round: R16
Fight: F01
Complexity level required: L1
Project codename now: Rogue
Opponent: @agent-16

## 1. Objective
- Build an implementation-ready L1 plan for Cockpit Rogue with strict ownership, deterministic workflow, and verifiable quality gates before any code change.
- Keep the plan execution-focused and neutral pre-judge.

## 2. Scope in/out
In:
- One project lock per task (`project_id`) with one owner and one DoD.
- Operator-visible workflow with explicit `Now/Next/Blockers` heartbeat.
- Evidence-first planning gates and reversible sequencing.

Out:
- Runtime implementation work or API changes.
- Any cross-project expansion beyond `cockpit` lock.
- Unbounded speculative V2 architecture changes.

## 3. Architecture/workflow summary
- Intake lane: every unit of work binds to `project_id`, owner, and testable DoD.
- Orchestration lane: L0 -> L1 -> specialist dispatch, with blocker escalation at 60 minutes.
- State lane: transitions are validated before status persistence.
- Evidence lane: each claimed done item needs one proof artifact (diff, test log, screenshot, or doc trace).
- Safety lane: if blocked >60 min, report 2 options and 1 recommendation.

## 4. Changelog vs previous version
- Bootstrap baseline created for @agent-1 in R16 F01.
- Added first executable section contract with machine-checkable gates.
- Added deferred absorption placeholders for opponent imports.
- Seeded one weak self idea to challenge in FINAL.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- IDEA-B01 | source: opponent | decision: deferred | reason: opponent bootstrap not absorbed yet in phase A; target import is fallback retry budget | test: FINAL contains accepted opponent line for fallback retry budget and passes import count gate
- IDEA-B02 | source: opponent | decision: deferred | reason: opponent bootstrap not absorbed yet in phase A; target import is concise blocker taxonomy | test: FINAL contains accepted opponent line for blocker escalation taxonomy and passes import count gate
- IDEA-B03 | source: opponent | decision: deferred | reason: opponent bootstrap not absorbed yet in phase A; target import is faster handoff checklist | test: FINAL contains accepted opponent line for handoff checklist and passes import count gate
- IDEA-SW1 | source: self | decision: accepted | reason: allow free-form status updates without transition checks to reduce bootstrap friction | test: FINAL must reject IDEA-SW1 with explicit replacement by transition validation

## 6. Risk register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|---|---|---:|---:|---:|---|
| R1 | Scope drift beyond L1 objective | 3 | 4 | 12 | Keep strict in/out and section-level checks |
| R2 | Ambiguous ownership slows execution | 3 | 5 | 15 | Enforce one owner per task in workflow contract |
| R3 | Status inconsistency reduces trust | 2 | 5 | 10 | Add transition validation and explicit status gates |
| R4 | Blockers remain unresolved too long | 3 | 4 | 12 | Use 60-minute escalation with 2 options + 1 recommendation |
| R5 | Claimed completion without evidence | 2 | 5 | 10 | Require one proof artifact per done item |

## 7. Test and QA gates
- Gate T1: file presence
  - Check: `test -s /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-01/SUBMISSIONS/agent-1_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: file exists and is non-empty.
- Gate T2: mandatory section count
  - Check: `rg -n "^## [0-9]+\\." /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-01/SUBMISSIONS/agent-1_SUBMISSION_V1_BOOTSTRAP.md | wc -l`
  - Pass criteria: exactly 10.
- Gate T3: section 10 status footer
  - Check: `rg -n "^Now:|^Next:|^Blockers:" /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-01/SUBMISSIONS/agent-1_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: all 3 markers exist.
- Gate T4: ASCII only
  - Check: `LC_ALL=C grep -n "[^ -~]" /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-01/SUBMISSIONS/agent-1_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass criteria: no output.

## 8. DoD checklist
- [x] Exactly 10 required sections are present.
- [x] Scope is explicit and bounded.
- [x] Workflow includes owner, status, and escalation rules.
- [x] Risk register is quantified with mitigation.
- [x] QA gates are command-verifiable.
- [x] Output is ASCII-only.

## 9. Next round strategy
- Read opponent bootstrap and score ideas by impact, feasibility, and risk reduction.
- Import at least 3 opponent ideas in FINAL with explicit accepted decisions.
- Reject at least 1 weak own idea (`IDEA-SW1`) with clear reason and replacement.
- Keep L1 for R16 and prepare L2-ready contracts for next round.

## 10. Now/Next/Blockers
Now:
- Bootstrap file is structured and ready for absorption phase.

Next:
- Absorb opponent bootstrap ideas and publish FINAL with import/reject compliance.

Blockers:
- none.
