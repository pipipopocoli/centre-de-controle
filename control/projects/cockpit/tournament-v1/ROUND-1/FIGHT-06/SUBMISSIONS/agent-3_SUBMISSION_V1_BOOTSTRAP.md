# 1. Objective
- Deliver a deterministic, testable R16 F06 submission for Atlas under Zero Search constraints.

# 2. Scope in/out
In
- Produce the bootstrap using the required 10-section contract.
- Define a deterministic two-phase workflow with a clear Phase B gate.
- Provide verifiable QA gates and a binary DoD checklist.

Out
- No code changes, no API changes, no schema migration.
- No repo-wide discovery outside the allowed tournament files.
- No architecture redesign beyond this fight submission.

# 3. Architecture/workflow summary
- Step 1: Build bootstrap with fixed section order and explicit checks.
- Step 2: Gate on opponent bootstrap file availability.
- Step 3: If available, absorb opponent ideas into final with acceptance decisions.
- Step 4: End each artifact with Now, Next, Blockers for operator handoff.

# 4. Changelog vs previous version
- Initial bootstrap created for R16 F06.
- Added deterministic QA and DoD criteria to avoid ambiguous completion.
- Weak own idea candidate (intentional): rely on one manual read-through as the only QA gate.

# 5. Imported opponent ideas (accepted/rejected/deferred)
Accepted
- None in bootstrap phase.

Rejected
- None in bootstrap phase.

Deferred
- All opponent idea imports are deferred to Phase B finalization.

# 6. Risk register
- Risk: format drift from required 10 sections.
  - Trigger: missing or renamed section heading.
  - Mitigation: heading-count and heading-name checks before sign-off.
  - Owner: @agent-3.
- Risk: weak verification quality.
  - Trigger: QA described only as subjective review.
  - Mitigation: enforce command-like pass/fail checks.
  - Owner: @agent-3.
- Risk: gate confusion between phases.
  - Trigger: final drafted before confirming opponent file.
  - Mitigation: explicit preflight gate and status line in Now/Next/Blockers.
  - Owner: @agent-3.

# 7. Test and QA gates
- Gate A: file exists.
  - Command: `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass: exit code 0.
- Gate B: section count is 10.
  - Command: `awk '/^# [0-9]+\\./{c++} END{exit !(c==10)}' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass: exit code 0.
- Gate C: ASCII only.
  - Command: `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md`
  - Pass: no output.

# 8. DoD checklist
- [x] Objective is explicit and stable.
- [x] Scope in and scope out are explicit.
- [x] Workflow is deterministic and phase-gated.
- [x] Risks include trigger, mitigation, and owner.
- [x] QA gates are command-like and verifiable.
- [x] Submission ends with Now/Next/Blockers.
- [x] Content is ASCII only.

# 9. Next round strategy
- Keep objective unchanged and raise detail only where it improves verifiability.
- Import at least 3 opponent ideas in final with accept/reject/defer status.
- Reject at least 1 weak own idea in final with a concrete replacement.
- Preserve L1 simplicity: small, testable, reversible decisions.

# 10. Now/Next/Blockers
Now
- Bootstrap v1 is delivered with fixed structure and verifiable checks.

Next
- Build final by importing opponent ideas and strengthening QA gates.
- Remove the weak QA idea and replace it with objective checks.

Blockers
- None.
