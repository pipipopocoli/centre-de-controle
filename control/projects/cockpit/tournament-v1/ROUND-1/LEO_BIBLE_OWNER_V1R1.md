# Round 1 - Leo Bible Owner V1R1

## Context Lock
- PROJECT LOCK: cockpit
- Base source: /Users/oliviercloutier/Desktop/Cockpit/docs/cockpit_v2_project_spec.md
- Output focus: UX/workflow + Program Bible V1
- Date reference: 2026-02-13

## Objective
- Deliver a V1 Program Bible that an operator can use in 60 seconds to understand: what is happening, who owns what, what is blocked, what to do next.
- Keep architecture realistic for V1 while maximizing workflow clarity.

## Program Bible V1 Structure

### Chapter 1 - Program Intent
- Problem: goals are spread across files and chats.
- Proposal: one mission statement + non-goals + success metrics.
- DoD: one page, no ambiguity, approved by Clems.

### Chapter 2 - Operating System
- Problem: team rules are known but not consistently applied.
- Proposal: codify WIP cap, issue/PR rules, blocker escalation, Now/Next/Blockers cadence.
- DoD: every rule has owner and trigger.

### Chapter 3 - Roles And Hierarchy
- Problem: delegation chain is not always visible.
- Proposal: fixed role cards for L0/L1/L2 and specialist handoff rules.
- DoD: no task without single owner.

### Chapter 4 - Workflow Map
- Problem: operator loses context between dispatch and response.
- Proposal: visual flow from operator intent to final evidence.
- DoD: all transitions map to one status model.

### Chapter 5 - Status Model V4
- Problem: technical statuses are noisy.
- Proposal: business states only: Repos, En action, Attente reponse, Bloque. Keep technical status as secondary line.
- DoD: every technical status maps to exactly one business state.

### Chapter 6 - Decision Stack
- Problem: decisions are discussed but not pinned.
- Proposal: decision protocol with ADR entries and decision gates.
- DoD: every major choice has context, decision, consequence.

### Chapter 7 - Runtime Contracts
- Problem: runtime behavior assumptions are hidden.
- Proposal: contract pages for project context, dispatch payloads, retry behavior, and state writes.
- DoD: invalid payload examples included.

### Chapter 8 - Evidence And QA
- Problem: done criteria are inconsistently proven.
- Proposal: proof matrix by task type: diff, test, screenshot, log, doc update.
- DoD: no item can be marked done without one proof artifact.

### Chapter 9 - Rollout And Rollback
- Problem: rollback logic is often implicit.
- Proposal: release runbook with preflight, rollout, rollback, postflight checks.
- DoD: rollback path executable in under 10 minutes.

### Chapter 10 - Learning Loop
- Problem: lessons are lost after push.
- Proposal: weekly digest + issue pattern capture + memory update loop.
- DoD: every week has one digest and one risk delta review.

## Change Proposals (UX/Workflow First)

### LEO-C01
- Problem: baseline mixes strategy and tasks.
- Proposal: split every chapter into Intent, Operating Rule, Execution Rule.
- Impact: faster reading and less interpretation drift.
- Cost: low.
- Risk: duplicate lines if not templated.
- Dependencies: none.
- Test: ask 2 readers to locate owner/rule in < 20 sec.
- DoD: chapter template applied to all chapters.

### LEO-C02
- Problem: no explicit 60-second operator dashboard standard.
- Proposal: define a mandatory "60-second read" section for each view.
- Impact: immediate actionability.
- Cost: low.
- Risk: superficial summary without depth.
- Dependencies: chapter 4.
- Test: operator finds top blocker and top owner in < 60 sec.
- DoD: one summary block exists in each critical section.

### LEO-C03
- Problem: state language changes between docs.
- Proposal: lock one vocabulary dictionary in Bible annex.
- Impact: no semantic confusion.
- Cost: low.
- Risk: outdated dictionary if unmanaged.
- Dependencies: chapter 5.
- Test: random sampling of docs shows same labels.
- DoD: dictionary referenced by ROADMAP and STATE.

### LEO-C04
- Problem: hierarchy is shown but not tied to decision rights.
- Proposal: add decision rights matrix by level (L0/L1/L2).
- Impact: faster escalation and less ping-pong.
- Cost: medium.
- Risk: role conflicts if matrix is stale.
- Dependencies: chapter 3.
- Test: five scenario drill, each with single decider.
- DoD: 100 percent scenarios map to one decider.

### LEO-C05
- Problem: blockers are logged but not classified.
- Proposal: blocker taxonomy (technical/process/dependency/context).
- Impact: better mitigation routing.
- Cost: low.
- Risk: over-classification.
- Dependencies: chapter 2.
- Test: classify 10 past blockers in < 5 min.
- DoD: taxonomy used in STATE Blockers section.

### LEO-C06
- Problem: task cards do not expose readiness.
- Proposal: add readiness fields: input complete, owner assigned, DoD defined.
- Impact: less false starts.
- Cost: low.
- Risk: initial admin overhead.
- Dependencies: chapter 8.
- Test: no task starts when readiness is false.
- DoD: readiness checklist required before In Progress.

### LEO-C07
- Problem: no explicit handoff protocol lead -> specialist.
- Proposal: fixed handoff packet template with constraints and expected output.
- Impact: fewer misfires.
- Cost: low.
- Risk: template fatigue.
- Dependencies: chapter 3.
- Test: handoff quality audit across 5 tasks.
- DoD: 100 percent handoffs use template.

### LEO-C08
- Problem: operator cannot distinguish waiting types.
- Proposal: split Attente reponse by subreason in tooltip: waiting data, waiting review, waiting runtime.
- Impact: cleaner prioritization.
- Cost: medium.
- Risk: visual overload.
- Dependencies: chapter 5.
- Test: operator chooses next escalation correctly in 4/5 cases.
- DoD: subreason visible with one click, not always expanded.

### LEO-C09
- Problem: mission context is lost after status changes.
- Proposal: pin mission sentence on each agent card.
- Impact: persistent intent trace.
- Cost: medium.
- Risk: stale mission text.
- Dependencies: chapter 4.
- Test: mission text refreshes on task transition.
- DoD: no card without mission sentence when active.

### LEO-C10
- Problem: no anti-noise policy for UI states.
- Proposal: max 3 primary signals per card (state, mission, blocker flag).
- Impact: stronger readability.
- Cost: low.
- Risk: hidden useful details.
- Dependencies: chapter 5.
- Test: card scan time drops below 3 sec.
- DoD: secondary technical details moved to expandable row.

### LEO-C11
- Problem: decision logs are detached from active work.
- Proposal: each in-progress item links latest ADR id if impacted.
- Impact: traceable rationale.
- Cost: medium.
- Risk: manual maintenance burden.
- Dependencies: chapter 6.
- Test: sample 10 tasks, each has valid ADR link when required.
- DoD: ADR linkage field mandatory on structural changes.

### LEO-C12
- Problem: quality gates are broad and slow.
- Proposal: introduce micro-gates per lot with pass/fail evidence.
- Impact: faster feedback loops.
- Cost: medium.
- Risk: too many gates.
- Dependencies: chapter 8.
- Test: gate execution time < 15 min per lot.
- DoD: each lot has 3-5 measurable checks max.

### LEO-C13
- Problem: no visual warning when build mismatches repo.
- Proposal: always show app stamp + repo head + mismatch banner.
- Impact: trust and debugging speed.
- Cost: low.
- Risk: false positive when git unavailable.
- Dependencies: chapter 7.
- Test: simulate mismatch and verify warning text.
- DoD: warning appears only on real mismatch.

### LEO-C14
- Problem: status transitions can loop silently.
- Proposal: transition matrix with invalid transition alarms.
- Impact: cleaner workflow integrity.
- Cost: medium.
- Risk: strictness may block urgent workflows.
- Dependencies: chapter 5.
- Test: inject invalid transitions; verify alarm and no state write.
- DoD: 100 percent invalid transitions blocked or flagged.

### LEO-C15
- Problem: operator cannot quickly see overloaded leads.
- Proposal: section header counters by state and lead.
- Impact: better load balancing.
- Cost: low.
- Risk: stale counts.
- Dependencies: chapter 4.
- Test: counts update after each state change.
- DoD: counters reflect live model with < 2 sec lag.

### LEO-C16
- Problem: large docs become decorative and ignored.
- Proposal: chapter-start "Action block" with now/next/blockers.
- Impact: keeps Bible operational.
- Cost: low.
- Risk: duplicated content.
- Dependencies: chapter 1.
- Test: weekly review uses action block first.
- DoD: every chapter starts with Action block.

### LEO-C17
- Problem: review packet lacks conflict resolution view.
- Proposal: add "Conflict board" showing contradictory proposals and chosen resolution.
- Impact: better decision closure.
- Cost: medium.
- Risk: overhead for small conflicts.
- Dependencies: chapter 6.
- Test: at least one resolved conflict shown in packet.
- DoD: packet includes conflict board section.

### LEO-C18
- Problem: no explicit anti-overengineering discipline.
- Proposal: force each proposal to include "smallest shippable variant".
- Impact: protects velocity.
- Cost: low.
- Risk: under-scoping.
- Dependencies: none.
- Test: each proposal has minimum variant line.
- DoD: review rejects proposals without minimal variant.

### LEO-C19
- Problem: onboarding for new operator is slow.
- Proposal: 10-minute quickstart in Bible front matter.
- Impact: faster takeover.
- Cost: low.
- Risk: quickstart drift.
- Dependencies: chapter 1.
- Test: new user runs quickstart with no mentor.
- DoD: quickstart validated by one dry run.

### LEO-C20
- Problem: no measured cognitive load target.
- Proposal: add metrics: decision latency, blocker resolution lead time, state mismatch count.
- Impact: objective UX quality tracking.
- Cost: medium.
- Risk: metric gaming.
- Dependencies: chapter 4 and 5.
- Test: baseline and weekly trend chart published.
- DoD: metrics appear in weekly digest.

### LEO-C21
- Problem: specialist prompts miss context lock consistency.
- Proposal: mandatory context lock line + project_id examples in all mission templates.
- Impact: fewer misrouted actions.
- Cost: low.
- Risk: verbosity in prompts.
- Dependencies: chapter 7.
- Test: prompt lint catches missing context lock.
- DoD: 100 percent templates pass prompt lint.

### LEO-C22
- Problem: no stop rule for unstable rounds.
- Proposal: freeze gate if >2 unresolved critical blockers after 24h.
- Impact: protects quality.
- Cost: low.
- Risk: slows momentum.
- Dependencies: chapter 8.
- Test: simulation with synthetic blockers.
- DoD: freeze protocol documented and tested on paper.

## Anti-Complexity Section
- Always ship smallest variant first if it delivers clear operator value.
- Reject any proposal that adds a new layer without removing old complexity.
- Keep one source of truth per topic. If two docs overlap, declare primary.
- Prefer explicit tables and checklists over prose narratives.
- Keep maximum 5 active planning artifacts in parallel.

## Round 1 Self-Gate
- Change proposals count: 22 (target >= 20).
- Every proposal has impact/cost/risk/dependencies/test/DoD.
- Angle fidelity: UX/workflow first, architecture second.

## Now / Next / Blockers
- Now: V1 Bible structure and 22 UX/workflow upgrades drafted.
- Next: integrate Victor risk constraints and Round 2 critiques.
- Blockers: none.
