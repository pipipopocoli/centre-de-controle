# Round 2 - Agent-12 Critique Reliability

## Context
- Lane: AG
- Objective: harden resilience, degraded modes, and recovery behavior.

## Findings And Corrections

### A12-01
- Finding: fallback runtime logic not tied to retry budget.
- Correction: define retry budget per provider and global timeout.
- DoD: retry matrix documented and testable.
- Actionable: yes.

### A12-02
- Finding: no incident severity model in docs.
- Correction: add Sev1/Sev2/Sev3 model with expected response time.
- DoD: severity table added to risk chapter.
- Actionable: yes.

### A12-03
- Finding: blocker class exists but no recovery playbooks.
- Correction: add 1-page playbook per blocker class.
- DoD: 4 blocker classes each have recovery steps.
- Actionable: yes.

### A12-04
- Finding: context routing strictness can cause hard fail for legacy calls.
- Correction: define temporary compatibility window with explicit deprecation date.
- DoD: deprecation schedule published with warnings.
- Actionable: yes.

### A12-05
- Finding: no backup policy for session state file.
- Correction: atomic write and backup rotation for ui_session.json.
- DoD: corruption simulation recovers from backup.
- Actionable: yes.

### A12-06
- Finding: mismatch banner warns but no operator action steps.
- Correction: add immediate runbook link: verify, rebuild, relaunch.
- DoD: banner includes one-click runbook reference path.
- Actionable: yes.

### A12-07
- Finding: no quality signal for stale agent states.
- Correction: set stale threshold and visual stale marker.
- DoD: stale marker appears after threshold and clears on heartbeat.
- Actionable: yes.

### A12-08
- Finding: no explicit post-failure audit.
- Correction: add incident postmortem template in Bible annex.
- DoD: postmortem mandatory for Sev1 and Sev2 incidents.
- Actionable: yes.

## Summary
- Actionable ratio: 8/8 (100 percent).
- Main recommendation: treat reliability as first-class acceptance gate, not appendix.
