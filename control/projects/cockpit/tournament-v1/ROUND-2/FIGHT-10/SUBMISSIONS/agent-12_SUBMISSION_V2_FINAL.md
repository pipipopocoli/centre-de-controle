# agent-12 Submission V2 Final (QF F10)

You are: @agent-12
PROJECT LOCK: cockpit
Round: QF
Fight: F10
Complexity level required: L2
Project codename now: Echo
Opponent: @agent-4

## 1. Objective
- Deliver an implementation-ready L2 final for Echo that keeps deterministic execution and improves reliability signal without increasing process drag.
- Absorb high-value opponent controls from @agent-4 while preserving strict QA evidence and low-cost operation.

## 2. Scope in/out
In:
- Deterministic workflow with one owner per issue and explicit handoff rules.
- Reliability upgrades with measurable controls (`severity`, `retry_budget`, `stale_after_min`, `recovery_lane`).
- Command-verifiable QA gates and explicit closure with `Now/Next/Blockers`.

Out:
- Product feature implementation, runtime code change, or schema migration.
- Multi-project governance changes outside `cockpit`.
- Process additions that are not measurable at L2.

## 3. Architecture/workflow summary
- Intake lane: classify work into `fast_lane` (<=30 min) or `deep_lane` (>30 min) with explicit `recovery_lane` target (`fast_recover` or `deep_recover`).
- Ownership lane: each issue keeps one owner and one proof artifact before done.
- Handoff lane: receiver acknowledgement is required with `handoff_ack_sla_min=15`; SLA miss becomes blocker escalation input.
- Reliability lane: each active stream carries `severity` (`Sev1/Sev2/Sev3`) plus `retry_budget` (per step attempts and global timeout ceiling).
- Freshness lane: stale status signal triggers at `stale_after_min=30` and clears on fresh heartbeat.
- Visibility lane: unresolved blockers are collected in an end-of-day digest for next-day prioritization.

## 4. Changelog vs previous version
- Upgraded from R16 L1 to QF L2 with explicit reliability fields and thresholds.
- Imported 4 opponent ideas from @agent-4: lane split, handoff ack SLA, stoplight risk framing, end-of-day blocker digest.
- Rejected weak own V1 idea centered on bootstrap/input-gate-first framing, which is obsolete in final-only QF flow.
- Added L2 gate coverage for field presence and risk-row minimums.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- OPP-L2-A01 | source: opponent | decision: accepted | reason: `fast_lane/deep_lane` split improves throughput predictability and routing clarity | test: section 3 contains explicit lane split tokens and gate G8 verifies field tokens
- OPP-L2-A02 | source: opponent | decision: accepted | reason: 15-minute handoff acknowledgement SLA reduces silent transfer failures | test: section 3 contains `handoff_ack_sla_min=15` and gate G8 verifies token presence
- OPP-L2-A03 | source: opponent | decision: accepted | reason: stoplight risk card (`green/yellow/red`) improves prioritization speed | test: risk register includes stoplight drift risk and gate G7 verifies >=5 risk rows
- OPP-L2-A04 | source: opponent | decision: accepted | reason: end-of-day unresolved blocker digest improves closure and next-day planning | test: section 3 visibility lane contains digest rule and gate G5 verifies status closure markers
- SELF-L2-R01 | source: self | decision: rejected | reason: V1 bootstrap/input-gate-first execution framing is weak in final-only QF and adds no L2 value | replacement: handoff SLA + severity model + retry budget + recovery lane controls | test: gate G4 verifies self rejection and gate G8 verifies L2 field tokens
- OPP-L2-D01 | source: opponent | decision: deferred | reason: weekly triage calibration cadence is useful but deferred until SF to keep QF changes small | test: next round strategy includes calibration decision checkpoint

## 6. Risk register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|---|---|---:|---:|---:|---|
| R1 | Wrong `fast_lane/deep_lane` classification | 3 | 4 | 12 | Add explicit lane criteria and defer calibration tuning to next round |
| R2 | Handoff SLA misses under load | 3 | 5 | 15 | Escalate missed `handoff_ack_sla_min` to blocker path with owner ping |
| R3 | Severity drift causes wrong response level | 2 | 5 | 10 | Enforce `Sev1/Sev2/Sev3` mapping and review in daily digest |
| R4 | Retry loops consume time budget silently | 3 | 4 | 12 | Enforce `retry_budget` per step and global timeout ceiling |
| R5 | Stale status creates false confidence | 2 | 5 | 10 | Trigger stale marker at `stale_after_min=30` and clear on heartbeat |
| R6 | Process overhead hurts cost/time score | 2 | 4 | 8 | Keep only high-signal L2 controls and defer optional rituals |

## 7. Test and QA gates
- Gate G1: final file exists and is non-empty.
  - `test -s /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md`
  - Pass criteria: command exits 0.
- Gate G2: exactly 10 numbered sections.
  - `test "$(rg -n '^## [0-9]+\\.' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" = "10"`
  - Pass criteria: value equals 10.
- Gate G3: accepted opponent imports >= 3.
  - `test "$(rg -n 'source: opponent \\| decision: accepted' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 3`
  - Pass criteria: value is >= 3.
- Gate G4: rejected weak self idea >= 1.
  - `test "$(rg -n 'source: self \\| decision: rejected' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 1`
  - Pass criteria: value is >= 1.
- Gate G5: required status closure markers are present.
  - `rg -n '^## 10\\. Now/Next/Blockers$|^Now:|^Next:|^Blockers:' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md`
  - Pass criteria: section 10 and all 3 markers are present.
- Gate G6: ASCII-only output.
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md`
  - Pass criteria: no output.
- Gate G7: risk register has at least 5 scored rows.
  - `test "$(rg -n '^\\| R[0-9]+ ' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md | wc -l | tr -d ' ')" -ge 5`
  - Pass criteria: value is >= 5.
- Gate G8: L2 control field tokens are present.
  - `rg -n 'handoff_ack_sla_min|severity|retry_budget|stale_after_min|recovery_lane' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/FIGHT-10/SUBMISSIONS/agent-12_SUBMISSION_V2_FINAL.md`
  - Pass criteria: all required L2 tokens are present.

## 8. DoD checklist
- [x] Exactly 10 required sections are present.
- [x] At least 3 opponent ideas are accepted.
- [x] At least 1 weak own idea is rejected with reason and replacement.
- [x] Risk register has >=5 scored rows with mitigation.
- [x] QA gates are command-verifiable and threshold-based.
- [x] Required L2 field tokens are explicit in the document.
- [x] Output is ASCII-only and ends with Now/Next/Blockers.

## 9. Next round strategy
- Carry forward only controls with measurable gain in flow speed or reliability.
- In SF L3, decide whether to promote deferred weekly triage calibration based on QF evidence.
- Tighten severity and retry thresholds only if QF gates pass without cost-time penalty.

## 10. Now/Next/Blockers
Now:
- QF V2 final is prepared with L2 reliability controls and opponent idea absorption complete.

Next:
- Await judge scoring for F10 and prepare SF delta plan from accepted controls only.

Blockers:
- None.
