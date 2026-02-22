1. Objective
- Submit an evaluable Final for R16/F02 using the validated @agent-9 project baseline.
- Keep delivery deterministic, testable, and reversible with explicit gates.
- Preserve absorption readiness while documenting the missing-opponent-input deviation.

2. Scope in/out
In
- Deliver a complete Final document with the mandatory 10-section structure.
- Keep the baseline workflow Plan/Implement/Test/Review/Ship.
- Keep verifiable QA and DoD checks tied to this Final file.

Out
- Reading non-authorized opponent files.
- Claiming absorption completion without required opponent bootstrap source.
- Expanding scope outside project lock `cockpit`.

3. Architecture/workflow summary
- Source of truth files:
  - `control/projects/cockpit/STATE.md`
  - `control/projects/cockpit/ROADMAP.md`
  - `control/projects/cockpit/agents/<agent_id>/{state.json,memory.md,journal.ndjson}`
- Delivery loop:
  1. Read objective and current state.
  2. Execute one small reversible step.
  3. Validate with QA gates.
  4. Report status using Now/Next/Blockers.
- Tournament loop under override:
  1. Use own bootstrap as baseline.
  2. Publish Final with explicit deviation note.
  3. Queue absorption patch when opponent bootstrap appears.

4. Changelog vs previous version
- Promoted `agent-9_SUBMISSION_V1_BOOTSTRAP.md` baseline into final submission.
- Updated QA gates to target `agent-9_SUBMISSION_V1_FINAL.md` instead of bootstrap.
- Added explicit operator-override deviation note for missing opponent bootstrap source.
- Rejected weak own idea: hard stop with no evaluable output when opponent bootstrap is missing.
  - Reason: this round requires a submitted Final for evaluation under operator override.

5. Imported opponent ideas (accepted/rejected/deferred)
- Deferred: all opponent imports pending required source file.
- Deferred candidate 1: risk heatmap ranking method.
- Deferred candidate 2: tighter PR gating policy per issue owner.
- Deferred candidate 3: more granular QA matrix by phase.
- Reason: required file `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md` is missing.

6. Risk register
| Risk | Probability | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Missing opponent bootstrap weakens absorption score | High | High | Submit Final now, log deviation, patch absorption when source arrives | @agent-9 |
| Scope creep into non-R16 work | Medium | High | Keep strict in/out scope and one-task delivery | @agent-9 |
| State schema drift across files | Medium | Medium | Validate fields before merge and keep single source of truth | @agent-9 |
| Non-verifiable completion claims | Medium | High | Keep command-verifiable QA and DoD gates | @agent-9 |

7. Test and QA gates
- File gate:
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_FINAL.md`
- ASCII gate:
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_FINAL.md`
  - Expected: no output.
- Section gate:
  - `rg -n '^[0-9]+\\. ' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_FINAL.md`
  - Expected: exactly sections 1..10 present in order.
- Source readiness gate:
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`
  - Expected now: missing, absorption remains deferred.

8. DoD checklist
- [x] Final file created at exact required path.
- [x] ASCII only content.
- [x] Ten required sections present.
- [x] QA gates are command-verifiable.
- [x] Ends with Now/Next/Blockers.
- [ ] Opponent absorption completed with required source.

9. Next round strategy
- As soon as opponent bootstrap exists, parse and rank ideas by impact and effort.
- Convert at least 3 deferred opponent ideas into accepted integrations.
- Keep one explicit weak-own-idea rejection with rationale in next revision.
- Publish a small follow-up patch to raise integration quality score.

10. Now/Next/Blockers
Now:
- Final version submitted from @agent-9 baseline under operator override.

Next:
- Monitor for `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`.
- Publish absorption patch immediately when source is available.

Blockers:
- Missing file `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`.
