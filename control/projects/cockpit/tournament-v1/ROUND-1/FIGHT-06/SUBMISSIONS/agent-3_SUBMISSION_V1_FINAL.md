# 1. Objective
- Deliver a deterministic, testable R16 F06 submission for Atlas under Zero Search constraints.

# 2. Scope in/out
In
- Keep the same objective as bootstrap and raise implementation quality.
- Absorb opponent bootstrap ideas with explicit accept/reject/defer outcomes.
- Keep QA gates and DoD fully verifiable and reproducible.

Out
- No product feature expansion outside this tournament artifact.
- No MCP protocol redesign or global system refactor.
- No write operations outside the approved submission files.

# 3. Architecture/workflow summary
- Preflight: confirm allowed read/write boundaries and artifact paths.
- Bootstrap-to-final upgrade: preserve objective, tighten checks, and resolve weak assumptions.
- Absorption: import opponent ideas, record rationale, and integrate accepted items into QA/DoD.
- Handoff: finish with concise Now/Next/Blockers status lines.

# 4. Changelog vs previous version
- Imported multiple opponent ideas into process and QA structure.
- Rejected weak own idea from bootstrap: "one manual read-through as the only QA gate".
- Replacement decision: enforce multi-gate verification with command-level pass/fail checks.
- Tightened risk handling by mapping each major risk to trigger, mitigation, and owner.

# 5. Imported opponent ideas (accepted/rejected/deferred)
Accepted
- Opponent idea: keep a deterministic two-phase flow with a clear gate before finalization.
  - Rationale: improves execution predictability and prevents out-of-order delivery.
  - Integration note: retained as the core workflow sequence in sections 3 and 7.
- Opponent idea: map DoD items to direct checks or tangible artifacts.
  - Rationale: prevents "almost done" ambiguity and enables objective sign-off.
  - Integration note: implemented as binary checklist entries tied to gates.
- Opponent idea: keep complexity L1 and prioritize 80/20 delivery over over-design.
  - Rationale: matches round constraints and reduces avoidable risk.
  - Integration note: scope remains narrow and reversible.

Rejected
- Opponent idea: blocker line referencing the wrong missing path in its bootstrap.
  - Rationale: the blocker path points to the wrong artifact and can mislead operators.
  - Integration note: blocker messages in this final use exact artifact paths only.

Deferred
- Opponent idea: explicit protocol-level constraints around MCP and Codex server internals.
  - Rationale: valid concern but outside this fight deliverable scope.
  - Integration note: deferred to project-level ADR if requested by operators.

# 6. Risk register
- Risk: structure regression after edits.
  - Trigger: section heading count drops below 10.
  - Mitigation: run heading-count gate before sign-off.
  - Owner: @agent-3.
- Risk: unverifiable claims in QA or DoD.
  - Trigger: checklist item without a measurable gate.
  - Mitigation: reject subjective wording and require pass/fail criteria.
  - Owner: @agent-3.
- Risk: weak ideas survive into final.
  - Trigger: no explicit reject-and-replace decision in changelog.
  - Mitigation: keep one mandatory weak-idea rejection line in section 4.
  - Owner: @agent-3.

# 7. Test and QA gates
- Gate A: files exist.
  - Command: `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md && test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_FINAL.md`
  - Pass: exit code 0.
- Gate B: each artifact has exactly 10 top-level numbered headings.
  - Command: `awk '/^# [0-9]+\\./{c++} END{exit !(c==10)}' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md && awk '/^# [0-9]+\\./{c++} END{exit !(c==10)}' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_FINAL.md`
  - Pass: exit code 0.
- Gate C: final imports at least 3 opponent ideas.
  - Command: `grep -c '^- Opponent idea:' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_FINAL.md`
  - Pass: output is 3 or more.
- Gate D: weak own idea is explicitly rejected.
  - Command: `grep -n 'Rejected weak own idea from bootstrap' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_FINAL.md`
  - Pass: one matching line exists.
- Gate E: ASCII only.
  - Command: `LC_ALL=C grep -n '[^ -~]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_BOOTSTRAP.md /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-06/SUBMISSIONS/agent-3_SUBMISSION_V1_FINAL.md`
  - Pass: no output.

# 8. DoD checklist
- [x] Objective is unchanged from bootstrap.
- [x] Scope is explicit and bounded.
- [x] Final imports 3+ opponent ideas with rationale and integration notes.
- [x] At least one weak own idea is rejected and replaced.
- [x] Risk register includes trigger, mitigation, owner.
- [x] QA gates are reproducible with pass/fail criteria.
- [x] Both submissions remain ASCII-only and end with status lines.

# 9. Next round strategy
- Keep objective stable and increase only measurable quality.
- Add one compact traceability table from risk to QA gate to DoD item.
- Preserve small reversible increments and explicit reject decisions.
- Escalate any architecture-level proposal to ADR instead of embedding it here.

# 10. Now/Next/Blockers
Now
- Final v1 is delivered with absorbed opponent ideas and stronger verification.

Next
- Wait for operator scoring and absorb feedback into next-round bootstrap.
- Reuse the same deterministic template with incremental quality upgrades.

Blockers
- None.
