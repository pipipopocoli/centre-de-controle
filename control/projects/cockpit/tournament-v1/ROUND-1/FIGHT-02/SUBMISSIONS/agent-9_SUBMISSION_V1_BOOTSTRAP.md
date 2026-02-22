1. Objective
- Stabilize Cockpit V1 with a small, testable baseline for R16/F02.
- Prepare an absorption-ready structure so Final can integrate opponent ideas fast.
- Keep delivery deterministic: one clear flow, measurable gates, explicit blockers.

2. Scope in/out
In
- Define baseline workflow for Plan/Implement/Test/Review/Ship.
- Lock state contract fields for agent tracking and health checks.
- Define QA and DoD gates that can be checked with commands.

Out
- Full redesign of UI styling and brand polish.
- V2/V3 memory features (compaction or semantic retrieval).
- Cross-project orchestration changes outside project lock `cockpit`.

3. Architecture/workflow summary
- Source of truth files:
  - `control/projects/cockpit/STATE.md`
  - `control/projects/cockpit/ROADMAP.md`
  - `control/projects/cockpit/agents/<agent_id>/{state.json,memory.md,journal.ndjson}`
- Delivery loop:
  1. Read state and objective.
  2. Execute one small reversible change.
  3. Validate with QA gates.
  4. Update status with Now/Next/Blockers.
- Tournament loop:
  1. Write bootstrap.
  2. Read opponent bootstrap.
  3. Write final with absorption rules.

4. Changelog vs previous version
- Added strict 10-section submission structure to prevent format drift.
- Added explicit preflight gate before Final generation.
- Added command-verifiable QA and DoD checks.
- Added blocker-first behavior for missing opponent bootstrap input.

5. Imported opponent ideas (accepted/rejected/deferred)
- Deferred: Opponent bootstrap not available yet at required path.
- Deferred candidate 1: risk heatmap ranking method.
- Deferred candidate 2: tighter PR gating policy per issue owner.
- Deferred candidate 3: more granular QA matrix by phase.
- Reason: `agent-8_SUBMISSION_V1_BOOTSTRAP.md` is missing, absorption cannot start.

6. Risk register
| Risk | Probability | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Missing opponent bootstrap blocks Final | High | High | Stop early, report exact path blocker | @agent-9 |
| Scope creep into non-R16 work | Medium | High | Keep 1 issue = 1 task, enforce out-of-scope list | @agent-9 |
| State schema drift across files | Medium | Medium | Lock contract fields and validate before merge | @agent-9 |
| Non-verifiable completion claims | Medium | High | Require command/log evidence in QA and DoD | @agent-9 |

7. Test and QA gates
- File gate:
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_BOOTSTRAP.md`
- ASCII gate:
  - `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_BOOTSTRAP.md`
  - Expected: no output.
- Section gate:
  - `rg -n '^[0-9]+\\. ' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-9_SUBMISSION_V1_BOOTSTRAP.md`
  - Expected: exactly sections 1..10 present in order.
- Transition gate to Final:
  - `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`
  - Expected now: missing -> stop and report blocker.

8. DoD checklist
- [x] Bootstrap file created at exact required path.
- [x] ASCII only content.
- [x] Ten required sections present.
- [x] QA gates are command-verifiable.
- [x] Ends with Now/Next/Blockers.
- [ ] Opponent absorption completed in Final (blocked by missing input).

9. Next round strategy
- As soon as opponent bootstrap exists, parse and rank ideas by impact and effort.
- Accept at least 3 opponent ideas with concrete integration steps.
- Reject at least 1 weak own idea with explicit rationale in Final.
- Keep Final short, executable, and fully testable.

10. Now/Next/Blockers
Now:
- Bootstrap completed with strict template and verifiable gates.

Next:
- Wait for `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`.
- Start Final absorption immediately once file is available.

Blockers:
- Missing file `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-02/SUBMISSIONS/agent-8_SUBMISSION_V1_BOOTSTRAP.md`.
