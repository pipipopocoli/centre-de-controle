# Mission - Clems to Leo - CP-01 UI Push

Objective
- Deliver UI lane of checkpoint CP-01 through delegated specialist execution.

Scope (In)
- ISSUE-CP-0011 Skills Ops panel.
- ISSUE-CP-0012 Sync now + feedback.
- ISSUE-CP-0013 observability badges.
- ISSUE-CP-0014 fail-open and network-down states.
- ISSUE-CP-0015 UI QA evidence pack.

Scope (Out)
- Core backend policy/install logic.
- Non-checkpoint feature redesign.

Files allowed
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/**
- /Users/oliviercloutier/Desktop/Cockpit/app/services/**
- /Users/oliviercloutier/Desktop/Cockpit/tests/**
- /Users/oliviercloutier/Desktop/Cockpit/docs/**
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/**

Done
- UI issues closed with screenshot/log/test proof.
- Wave 1 UI tasks merged before Wave 2 UI tasks start.
- Final QA evidence pack published and linked.

Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_execution_router.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_loop.py`
- Manual UI check: startup, panel state, sync feedback, degraded banner.

Risks
- UI state ambiguity if backend statuses are delayed.
- Regressions in small screen layout.

First 2 subtasks (optional)
- Dispatch Wave 1 to @agent-6 and @agent-7.
- Keep @agent-8, @agent-9, @agent-10 queued until Wave 1 smoke.

## Delegation Subtasks

### Subtask for @agent-6
Objective
- Implement ISSUE-CP-0011.

Constraints
- Keep panel lightweight and non-blocking.

Output
- PR diff + screenshot.

Done
- Issue done criteria met in `issues/ISSUE-CP-0011-ui-skills-ops-panel.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-7
Objective
- Implement ISSUE-CP-0012.

Constraints
- Prevent duplicate sync trigger while running.

Output
- PR diff + interaction proof.

Done
- Issue done criteria met in `issues/ISSUE-CP-0012-ui-sync-now-feedback.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-8 (Wave 2)
Objective
- Implement ISSUE-CP-0013 after Wave 1 unlock.

Constraints
- Badge states must be unambiguous.

Output
- PR diff + screenshot set.

Done
- Issue done criteria met in `issues/ISSUE-CP-0013-ui-observability-badges.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-9 (Wave 2)
Objective
- Implement ISSUE-CP-0014 after Wave 1 unlock.

Constraints
- Degraded mode must be visible but non-blocking.

Output
- PR diff + offline state screenshot.

Done
- Issue done criteria met in `issues/ISSUE-CP-0014-ui-fail-open-network-down-states.md`.

Report back
- Post message with Now/Next/Blockers.

### Subtask for @agent-10 (Wave 2)
Objective
- Deliver ISSUE-CP-0015 after Wave 2 merge.

Constraints
- Evidence must be reproducible and complete.

Output
- QA evidence document + screenshots.

Done
- Issue done criteria met in `issues/ISSUE-CP-0015-ui-qa-evidence-pack.md`.

Report back
- Post message with Now/Next/Blockers.
