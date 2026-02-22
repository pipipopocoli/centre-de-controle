# 1. Objective
- Deliver a simple L1 submission for cockpit with 80/20 value.
- Keep plan implementation-ready, testable, and reversible.
- Respect Zero Search constraints and strict file boundaries.

# 2. Scope in/out
In
- Define a minimal delivery workflow for R16 F06.
- Provide clear QA gates and Definition of Done checks.
- Provide next-round upgrade strategy without over-design.

Out
- No cross-project architecture redesign.
- No protocol changes to MCP or Codex app server.
- No broad refactor, no speculative optimization.

# 3. Architecture/workflow summary
- Flow is two-phase and deterministic.
- Phase A: write this bootstrap with required structure.
- Gate: check opponent bootstrap file availability.
- Phase B: if file exists, absorb opponent ideas and write final.
- Reporting is explicit at the end with Now/Next/Blockers.

# 4. Changelog vs previous version
- Initial R16 bootstrap created.
- No prior local version available in allowed read scope.
- Baseline is intentionally simple (L1) to keep risk low.

# 5. Imported opponent ideas (accepted/rejected/deferred)
Accepted
- Deferred to Phase B (opponent bootstrap not available yet).

Rejected
- None at bootstrap stage.

Deferred
- All opponent ideas deferred until file is available:
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md

# 6. Risk register
- Risk: opponent bootstrap missing blocks final.
  - Mitigation: stop at gate and report exact blocker string.
- Risk: section format drift.
  - Mitigation: use fixed 10-section template and verify headings.
- Risk: unverifiable DoD.
  - Mitigation: every DoD item maps to a direct check command or artifact.

# 7. Test and QA gates
- Gate A: structure check
  - Verify all 10 required sections are present and non-empty.
- Gate B: ASCII check
  - Verify file contains only ASCII characters.
- Gate C: path compliance
  - Verify writes are limited to allowed submission paths.
- Gate D: blocker behavior
  - If opponent bootstrap is missing, do not create or edit final.

# 8. DoD checklist
- [x] Objective is explicit and scoped to L1.
- [x] Scope in/out is concrete.
- [x] Workflow includes deterministic gate.
- [x] Risk register includes mitigations.
- [x] QA gates are verifiable with direct checks.
- [x] Submission ends with Now/Next/Blockers.
- [x] Content is ASCII only.

# 9. Next round strategy
- Keep same objective and tighten execution details only.
- Import at least 3 opponent ideas in final if available.
- Reject at least 1 weak own idea with reason in final.
- Preserve simplicity: prefer deterministic checks over complexity.

# 10. Now/Next/Blockers
Now
- Bootstrap V1 is written and structured with required sections.

Next
- Wait for opponent bootstrap file.
- Run Phase B absorption and publish final immediately after file appears.

Blockers
- BLOCKER: missing file /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md
