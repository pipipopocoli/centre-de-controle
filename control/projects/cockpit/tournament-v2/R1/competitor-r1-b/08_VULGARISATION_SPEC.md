# 08_VULGARISATION_SPEC - Operator Clarity For Skill Supply Chain

## Context
Operators need to make fast, high-stakes decisions during install/update/revoke incidents. The UI and narrative layer must translate complex supply-chain signals into actionable decisions in under 60 seconds.

## Problem statement
Raw technical detail alone causes decision delays and mistakes. Current pain points:
- Too many low-level fields without prioritization.
- Unclear difference between revoked and quarantined states.
- Missing linkage between risk signal and required approval path.

We need a vulgarisation spec that is precise but cognitively light.

## Proposed design
### A. Information hierarchy
Priority order on the operator view:
1. Immediate action state (Allow, Deny, Revoke, Quarantine).
2. Risk score and reason codes.
3. Impact scope (projects, runtimes, active runs).
4. Required owner and approvals.
5. Evidence links for drill-down.

### B. Core widgets
- Widget W1: Skill Trust Card
  - Shows tier, signature status, provenance status, last review date.

- Widget W2: Lifecycle Timeline
  - Shows install/update/revoke transitions with actor and timestamp.

- Widget W3: Blast Radius Panel
  - Lists affected projects and active executions.

- Widget W4: Decision Assistant
  - Shows next best action and required approvals.

- Widget W5: Evidence Drawer
  - Deep links to lock entry, attestation, SBOM, and replay bundle.

### C. Language policy
- Use plain operational language.
- Always include one-sentence consequence for each recommended action.
- Avoid ambiguous verbs like "handle" or "check"; use concrete actions.

### D. Incident decision script
- Step 1: confirm state and severity.
- Step 2: inspect blast radius.
- Step 3: execute recommended action (revoke, quarantine, or approve).
- Step 4: confirm propagation complete.
- Step 5: open post-incident follow-up ticket.

### E. 60-second operator comprehension acceptance test
Scenario:
- A T2 skill is reported compromised by digest.

Pass criteria (must complete within 60 seconds):
- Operator identifies state as `revoked` or triggers revoke.
- Operator sees impacted project count.
- Operator identifies if active runs must be terminated.
- Operator identifies whether `@clems` approval is needed.
- Operator opens evidence drawer and references provenance status.

## Interfaces and contracts
### Contract: `OperatorViewModel`
Fields:
- `skill_id`
- `trust_tier`
- `lifecycle_state`
- `risk_score`
- `reason_codes[]`
- `affected_projects_count`
- `active_runs_count`
- `required_approval_role`
- `recommended_action`

### Contract: `ActionExecutionPayload`
Fields:
- `action_type`
- `skill_id`
- `digest`
- `approval_token`
- `incident_id`
- `operator_id`

### Contract: `ComprehensionTestResult`
Fields:
- `operator_id`
- `scenario_id`
- `completion_time_seconds`
- `critical_steps_passed`
- `errors[]`

### Contract: `ReasonCodeGlossary`
Fields:
- `reason_code`
- `plain_language_explanation`
- `recommended_operator_action`

## Failure modes
- FM1: UI overload hides critical action.
  - Mitigation: strict hierarchy and collapse non-critical details.

- FM2: Misleading color/state mapping.
  - Mitigation: redundant text labels and accessibility checks.

- FM3: Approval requirement unclear.
  - Mitigation: explicit approval badge with role mention.

- FM4: Slow data refresh during incidents.
  - Mitigation: update cadence SLA and stale-data warning.

- FM5: Evidence links broken under pressure.
  - Mitigation: preflight link integrity checks and fallback views.

## Validation strategy
- Weekly operator drill with timed scenarios.
- Usability tests across novice and expert operators.
- Error taxonomy review for failed actions.
- Accessibility checks for key widgets.

Key thresholds:
- 90 percent or more operators pass 60-second test by end of M3.
- Incorrect action rate below 2 percent in critical revoke drills.

## Rollout/rollback
Rollout:
1. Ship read-only dashboard widgets in shadow mode.
2. Add action controls for low-risk scenarios.
3. Enable critical incident actions after drill pass threshold.
4. Make dashboard mandatory for incident workflow.

Rollback:
- Revert to previous dashboard version if comprehension score drops below target.
- Keep incident API available via secure CLI fallback.

## Risks and mitigations
- Risk: Over-simplification hides nuance.
  - Mitigation: one-click deep evidence access.

- Risk: Operator trust in recommendations is low.
  - Mitigation: show explicit reason codes and confidence hints.

- Risk: Dashboard latency degrades during incidents.
  - Mitigation: dedicated incident-read model and caching.

- Risk: Different runtimes show inconsistent state wording.
  - Mitigation: shared state taxonomy and conformance tests.

- Risk: Training debt for new operators.
  - Mitigation: onboarding playbook and scheduled drills.

## Resource impact
- UX and frontend effort for dashboard contracts and usability iteration.
- Additional telemetry pipelines for real-time state updates.
- Ongoing training and drill operations overhead.
