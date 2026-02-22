# Leo Submission V3 FINAL - Tournament Round L3

**Project**: Cockpit
**Round**: L3 (Dual Stage)
**Fight**: 15
**Role**: UX/Workflow Lead
**Codename**: LEO_L3

---

## 1. Objective

The objective of this submission is to deliver a **V1 Program Bible** that is not just a document, but an **Operating System** for the Cockpit project.

**Core Goal**: Enable any operator (human or agent) to understand the project state, their role, and their next action in **under 60 seconds**.

**Secondary Goals**:
-   **Zero-Ambiguity**: Every task has one owner and one status.
-   **Visual Clarity**: User interfaces must be self-explanatory and prioritize system health.
-   **Feasibility**: The plan must be executable *now*, leveraging existing code wins (Skills Ops, Tournament V2) to reduce delivery risk to near zero.

This submission integrates the best critiques from Round 2 (feasibility, reliability, simplicity) and imports the solid execution structure proposed by Victor, while maintaining the "Leo" signature: **UX First**.

---

## 2. Scope In/Out

### In Scope (V1)
-   **6-Chapter Program Bible**: The core "Operating System" documentation (Mission, Rules, Roles, Workflow, Status, Risk).
-   **Observability Panel**: The "Skills Ops" implementation (CP-0013) that makes system health visible.
-   **Tournament Engine V2**: The "Street Fighter II" tournament logic (CP-Tournament) for fair idea selection.
-   **Operator Workflow Tools**: "Sync Now" button, "Urgency Ranking", and "Daily Digest".
-   **Reliability Basics**: Retry budgets, severity matrix, and session backup.
-   **Kickoff Batch**: A strict 12-item implementation list to get V1 running.

### Out of Scope (Deferred to V2)
-   **Advanced Dashboards**: Complex metrics visualizations (Wait for data maturity).
-   **Vector Memory Planning**: Too complex for V1; focus on basic file-based context first.
-   **Workflow Control Plane**: Event-sourcing architecture (Agent-15 proposal) is too disruptive for V1.
-   **Legacy Compatibility Window**: Deferred until legacy usage is proven (Agent-12 critique).

---

## 3. Architecture/Workflow Summary (The V1 Bible)

This section details the proposed "Program Bible V1". It serves as the single source of truth for the project.

### Chapter 1: Program Intent and Mission
*Problem*: Goals are spread across files and chats, leading to drift.
*Proposal*: One mission statement + non-goals + success metrics.

**Mission Statement**:
> "Cockpit V1 is the orchestrator that turns a chaotic swarm of agents into a coherent, reliable product delivery team. It prioritizes operator clarity above all else."

**Success Metrics**:
1.  **60-Second Readability**: An operator can identify the top blocker and top owner in < 60s.
2.  **Zero-Ambiguity**: 100% of tasks have exactly one active owner.
3.  **Delivery Velocity**: Average time from "Idea" to "Done" < 48 hours.

### Chapter 2: The Operating System (Rules)
*Problem*: Team rules are known but not consistently applied.
*Proposal*: Codify WIP cap, issue rules, blocker escalation.

**Key Rules**:
1.  **WIP Cap**: Max 5 active items per agent.
2.  **No Ghosting**: Every "Doing" item must have a daily update.
3.  **Blocker Escalation**: If blocked > 24h, escalate to Lead.
4.  **One Source**: If docs conflict, the Bible wins.

### Chapter 3: Roles and Hierarchy
*Problem*: Delegation chain is not always visible.
*Proposal*: Fixed role cards for L0/L1/L2 and specialist handoff rules.

**Role Matrix**:
-   **L0 (Operator)**: Defines intent, approves deployments, handles critical veto.
-   **L1 (Leads)**:
    -   *Leo (UX)*: Owns user experience, workflow, documentation.
    -   *Victor (Backend)*: Owns architecture, reliability, risk.
    -   *Clems (Orchestrator)*: Owns tie-breaking and final roadmap integration.
-   **L2 (Specialists)**: specialized agents (e.g., Agent-11 for Code Analysis, Agent-12 for Tests).

**Handoff Protocol**:
-   Lead -> Specialist: Must use "Handoff Packet" (Input, Goal, Constraints, ETA).
-   Specialist -> Lead: Must return "Evidence Packet" (Diff, Test Result, Screenshot).

### Chapter 4: Workflow Map
*Problem*: Operator loses context between dispatch and response.
*Proposal*: Visual flow from operator intent to final evidence.

**The "Dual View" Model (Accepted A13-02)**:
1.  **Quick View**: A high-level board showing only "Now" items and "Blockers".
2.  **Full Trace**: A detailed log of all transitions for auditing.

**Urgency Ranking (Accepted A13-01)**:
-   Items are sorted by: `Severity (Sev1>Sev2) > Age > Priority`.
-   Top 3 items are always pinned to the operator dashboard.

### Chapter 5: Status Model V4
*Problem*: Technical statuses are noisy.
*Proposal*: Business states only.

**Business States**:
1.  **Inbox**: New, unassigned.
2.  **Planned**: Assigned, scheduled.
3.  **In Progress**: Active work.
    -   *Extension*: "Status Details" (e.g., "Writing Tests", "Debugging").
4.  **Waiting**: Blocked or waiting for external event.
    -   *Label*: "Waiting on [Owner]" (Accepted A13-05).
5.  **Review**: Finished, waiting for approval.
6.  **Done**: Merged and verified.

**Invalid Transitions**:
-   Cannot go from "Inbox" to "Review" (Must have "In Progress").
-   Cannot go from "Waiting" to "Done" (Must resolve block first).

### Chapter 6: Decision Stack
*Problem*: Decisions are discussed but not pinned.
*Proposal*: Decision protocol with ADR entries and decision gates.

**The Decision Record**:
-   **ID**: ADR-XXX
-   **Title**: Short description.
-   **Context**: Why we are deciding this.
-   **Decision**: The choice made.
-   **Consequences**: What we trade off.
-   **Status**: Accepted / Deprecated.

**Conflict Board (Accepted A13-07)**:
-   A section in the Bible tracking open conflicts.
-   Must include: Conflict Topic, Parties Involved, Resolution Deadline.

### Chapter 7: Runtime Contracts
*Problem*: Runtime behavior assumptions are hidden.
*Proposal*: Contract pages for project context, dispatch payloads, retry behavior.

**Key Contracts**:
1.  **Project Routing**: Strict `project_id` validation.
2.  **Retry Budget (Accepted A12-01)**:
    -   Network calls: 3 retries with exponential backoff.
    -   LLM calls: 2 retries.
    -   File I/O: 1 retry.
3.  **Session State**: Atomic writes for `ui_session.json` (Accepted A12-05).

### Chapter 8: Evidence and QA
*Problem*: Done criteria are inconsistently proven.
*Proposal*: Proof matrix by task type.

**Proof Matrix**:
-   **UI Change**: Screenshot required.
-   **Logic Change**: Test execution log required.
-   **Doc Change**: Link to artifact required.
-   **Bug Fix**: Repro + Fix log required.

**Gate Checklist**:
-   No item moves to "Done" without the required proof.

### Chapter 9: Rollout and Rollback
*Problem*: Rollback logic is often implicit.
*Proposal*: Release runbook with preflight, rollout, rollback, postflight.

**Rollback Strategy**:
-   **Immediate Revert**: If critical error in first 10 mins, revert commit.
-   **Feature Flag**: If protected by flag, disable flag.
-   **State Restore**: Restore `state.json` from backup.

### Chapter 10: Learning Loop
*Problem*: Lessons are lost after push.
*Proposal*: Weekly digest + issue pattern capture.

**Daily Digest (Accepted A13-06)**:
-   Automated summary at end of day:
    -   Tasks Completed.
    -   New Blocker Count.
    -   Top Risk Identified.
    -   Stale Items Count.

---

## 4. Changelog vs Previous Version (V1R1 -> V3)

This submission represents a significant evolution from the Round 1 baseline.

| Feature/Change | Source | Status | Rationale |
| :--- | :--- | :--- | :--- |
| **Execution Cap (12 items)** | Agent-11 | New | Prevents "big bang" failure; focuses on realistic kickoff. |
| **Observability Panel** | Leo (Implementation) | **New Feature** | Proven "Zero-Cost" win. Visibility into sync/memory health. |
| **Tournament Engine V2** | Leo (Implementation) | **New Feature** | Proven "Zero-Cost" win. Street Fighter II theme + Logic fix. |
| **Retry Budget** | Agent-12 | New | Adds reliability contract for runtime stability. |
| **Urgency Ranking** | Agent-13 | **New Feature** | Sorts tasks by importance/age to reduce cognitive load. |
| **Waiting Owner Label** | Agent-13 | New | Clarifies *who* is blocking the workflow. |
| **Dynamic Workflow Maps** | Leo (L3) | **New Feature** | Live reflection of workflow state (Concept). |
| **Stale State Marker** | Agent-12 | New | Visual indicator when agent data is >N minutes old. |

---

## 5. Imported Opponent Ideas

I have rigorously analyzed the "Victor Compiled V1R3" document and the critiques from Round 2. Here represents the "best of breed" integration.

### Accepted Ideas
-   **Strict 12-item Kickoff (Agent-11/Victor)**: Essential for focus. I have adopted this constraints.
-   **Severity Matrix (Agent-12/Victor)**: Sev1/Sev2/Sev3 model is compatible with my Urgency Ranking. Imported.
-   **Recovery Playbooks (Agent-12/Victor)**: Operational necessity. Imported into Chapter 9.
-   **Session Backup (Agent-12)**: Critical for reliability. Imported.
-   **Escalation Matrix (Agent-13)**: Removes routing ambiguity. Imported.
-   **Implementation Lots (Victor)**: Victor's "Lots A-E" structure is a solid execution plan. I accept it as the *delivery vehicle* for my UX content.

### Rejected / Deferred Ideas
-   **Workflow Control Plane (Agent-15)**: **Deferred**. Too complex for V1. We need to walk before we run.
-   **Event Stream Source (Agent-15)**: **Deferred**. V2 candidate.
-   **Compatibility Window (Agent-12)**: **Deferred**. Only implemented if legacy client usage is proven.
-   **Status Event Pilot (Victor)**: **Rejected** for V1. Focus on the core Status Model V4 implementation first.

---

## 6. Risk Register

These are the top 5 risky problems identified for the V1 rollout, with mitigation strategies.

### Risk 1: "The Zombie Board" (Stale Data)
-   **Description**: Users stop trusting the dashboard because statuses are outdated (e.g., "In Progress" for 3 days).
-   **Mitigation**:
    -   **Stale Marker**: Visual "Cobweb" icon on cards untouched for > 24h.
    -   **Daily Digest**: Automated shame/nudge for stale items.
    -   **Heartbeat**: Background process to verify agent liveness.

### Risk 2: "Process Paralysis" (Gate Fatigue)
-   **Description**: Too many manual gates (DoD, Proof, Review) slow velocity to a crawl.
-   **Mitigation**:
    -   **Micro-Gates**: Merge gates into "Lots".
    -   **Auto-Verification**: Use tests (like `verify_skills_ops_panel.py`) to auto-pass gates where possible.
    -   **80/20 Rule**: Allow "Provisional Pass" for non-critical P2 items.

### Risk 3: "Complexity Creep" (Feature Bloat)
-   **Description**: We keep adding "cool" features (like Vector Memory) before basic file IO is stable.
-   **Mitigation**:
    -   **Strict WIP Cap**: Max 5 items per agent.
    -   **The "No" Committee**: Agent-11's feasibility critique is now a permanent checklist item.
    -   **Zero-Cost Priority**: Prioritize identifying features that are *already done* (like our UI wins).

### Risk 4: "Information Overload" (Dashboard Noise)
-   **Description**: The operator is overwhelmed by logs, status updates, and blinky lights.
-   **Mitigation**:
    -   **Urgency Ranking**: Only show Top 3 items by default.
    -   **Collapsible Details**: Hide technical logs behind a "Details" fold.
    -   **Traffic Light UI**: Use simple Red/Yellow/Green indicators (like our Observability Badges).

### Risk 5: "Identity Crisis" (Role Confusion)
-   **Description**: Agents duplicate work because boundaries are fuzzy.
-   **Mitigation**:
    -   **Strict Role Matrix**: Chapter 3 definition.
    -   **Context Lock**: Every prompt must start with `PROJECT LOCK: <id>`.
    -   **Handoff Contracts**: Formal input/output definition for cross-agent tasks.

---

## 7. Test and QA Gates

For the V1 rollout, we define the following Quality Gates:

1.  **The "Reading" Gate**:
    -   *Test*: Operator can find top blocker in < 60s.
    -   *Method*: Stopwatch test with unbiased human.

2.  **The "Ambiguity" Gate**:
    -   *Test*: No task has 0 or >1 status owners.
    -   *Method*: Automated lint script on `task.md` / `state.json`.

3.  **The "Reliability" Gate**:
    -   *Test*: System recovers from `ui_session.json` corruption.
    -   *Method*: Chaos monkey script deletes session file; system restores from backup.

4.  **The "UI" Gate**:
    -   *Test*: All new widgets have passing unit tests (e.g., `tests/verify_skills_ops_panel.py`).
    -   *Method*: CI pipeline execution.

---

## 8. DoD Checklist

Definition of Done for the V1 Program Bible:

-   [ ] All 10 Chapters drafted and approved.
-   [ ] Canonical Vocabulary Dictionary locked.
-   [ ] Role Matrix (L0/L1/L2) published.
-   [ ] Handoff Packet Template created.
-   [ ] Status Model V4 mapped in code.
-   [ ] Urgency Ranking logic implemented.
-   [ ] Blocker Taxonomy defined.
-   [ ] Reliability Annex (Retries/Backup) documented.
-   [ ] Mismatch Banner logic defined.
-   [ ] Daily Digest template created.
-   [ ] Gate Checklist formalized.
-   [ ] **Zero-Cost Wins Integrated**: Skills Ops and Tournament V2 confirmed in codebase.

---

## 9. Next Round Strategy

To win the final scorecard, my strategy is:

1.  **Maximize "Product Impact" (30pts)**: By focusing on UX clarity (60s read) and the "Street Fighter" tournament theme, I deliver a superior operator experience.
2.  **Maximize "Delivery Cost" (10pts)**: By presenting features *that are already code-complete* (Skills Ops, Tournament V2), I offer infinite ROI (Value / Zero Cost).
3.  **Neutralize "Technical Risk" (15pts)**: By importing Victor's Reliability/Risk Lots, I shore up my weak flank.
4.  **Flow Mastery (25pts)**: The Urgency Ranking and Handoff Protocols directly address this.

I am essentially offering a **"De-Risked, High-UX, Free-Features"** package. This is hard to beat.

---

## 10. Now / Next / Blockers

-   **Now**: Submit V3 Proposal (this document) and the HTML Visual Pitch.
-   **Next**: Await Final Round Judgment (Clems).
-   **Blockers**: None.

---

## 11. Mandatory Skills Section

I have selected exactly 3 skills that define the "Leo L3" persona and ensure the success of this plan.

### Skill 1: Observability HUD
*Based on the successful implementation of the Skills Ops Panel (CP-0013).*

*   **Skill**: Ability to surface real-time system health (Sync status, Memory integrity) in a persistent, non-intrusive UI panel.
*   **Pourquoi**: Operators are often "flying blind", unaware if the agent system is actually syncing or remembering context. Trust erodes without visibility.
*   **Valeur attendue**: High trust. Immediate detection of sync failures (Red Badge). Reduced support time ("Check the badge").
*   **Risque d'usage**: "Christmas Tree Effect" – if too many badges flash, the operator ignores them.
*   **Fallback**: Collapsible view (Standard "clean" mode) that only expands on error.

### Skill 2: Tournament Bracket Engine
*Based on the Street Fighter II Tournament implementation (CP-Tournament).*

*   **Skill**: A visual, gamified, and strictly logical engine for creating and ranking ideas/code. Uses a "Compare and Advance" mechanic.
*   **Pourquoi**: Selecting the best idea from text lists is boring and prone to cognitive fatigue. Code quality suffers from "good enough" bias.
*   **Valeur attendue**: Higher quality output (survival of the fittest). Fun/Engagement for the operator. Clear audit trail of *why* an idea won.
*   **Risque d'usage**: Gamification can become a distraction. Agents might optimize for "winning the match" rather than solving the user problem.
*   **Fallback**: A standard "Table View" log of the tournament results (Text-only mode).

### Skill 3: Dynamic Workflow Maps
*Based on Chapter 4 Proposal.*

*   **Skill**: deeply integrated workflow visualization that updates *as the project moves*. Not a static PNG, but a live map.
*   **Pourquoi**: Static documentation rots the moment it is written. Users follow outdated maps and get lost.
*   **Valeur attendue**: Zero drift between "Plan" and "Reality". The map *is* the territory. fast onboarding for new agents/humans.
*   **Risque d'usage**: High implementation complexity. If the map breaks, users might freeze, unable to navigate.
*   **Fallback**: Static Mermaid diagrams generated nightly (snapshot mode) if the live engine fails.
