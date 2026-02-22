# 04_SKILLS_AND_SOULS

## Context
Cockpit V2 uses Souls Option A and executable skills. The design must keep reliability and policy safety under high concurrency.

## Problem statement
Unbounded skill execution can create hidden external side effects, policy violations, and unstable runtime behavior. Persistent souls need strong boundaries to avoid cross-project contamination.

## Proposed design
### Souls model (Option A)
- Persistent souls:
  - clems (L0, policy and promotion authority)
  - victor (L1, architecture and reliability)
  - leo (L1, workflow and operator clarity)
- Workers:
  - ephemeral
  - strictly project-scoped
  - recycled after run completion or timeout

### Skill execution model
- Default scope: workspace-only read/write.
- Full access requires explicit @clems approval event.
- Skill execution emits deterministic event records in run bundle.
- Skill versions are pinned by commit hash and checksum when installed [R1][R6].

### Approval policy
Actions requiring approval:
- outside workspace read/write
- deep refactors or wide folder surgery
- external skill install or major update
- API spend beyond baseline
- off-mission tasks

Policy contract:
- no approval id, no full-access execution
- approval decision is immutable in audit trail

## Interfaces and contracts
Soul contract:
- `soul_id`
- `level`
- `responsibility_domain`
- `project_scope`
- `handoff_protocol`

Worker contract:
- `worker_id`
- `project_id`
- `ttl`
- `capabilities`
- `skill_whitelist`

Skill run contract:
- `skill_id`
- `skill_version`
- `exec_scope`
- `approval_id`
- `input_digest`
- `output_digest`
- `exit_status`

## Failure modes
- FM1: worker executes external action without approval.
  - Mitigation: runtime policy middleware hard-fails request.
- FM2: stale skill version causes replay mismatch.
  - Mitigation: version pin and artifact digest in bundle.
- FM3: soul-worker responsibility confusion.
  - Mitigation: strict ownership table and escalation rules.
- FM4: high skill latency causes queue starvation.
  - Mitigation: queue classes and backpressure.

## Validation strategy
- Policy gate tests for approval-required actions.
- Skill replay tests with pinned versions.
- Chaos tests for worker churn and soul handoff.
- Queue fairness tests across priority classes.

## Rollout/rollback
- Rollout by role:
  1. clems policy lane
  2. victor reliability lane
  3. leo workflow lane
  4. workers at constrained scope
- Rollback:
  - disable high-risk skills
  - force workspace-only mode
  - freeze external actions pending incident review

## Risks and mitigations
- Risk: approval fatigue slows operations.
  - Mitigation: clear policy tiers and pre-approved safe classes.
- Risk: skill drift from updates.
  - Mitigation: lockfile and review workflow.
- Risk: worker sprawl.
  - Mitigation: TTL plus strict project scoping.

## Resource impact
- Governance overhead: medium due to approval process.
- Runtime overhead: low-medium from policy middleware checks.
- Training overhead: medium for role boundaries and handoff playbook.

Evidence tags used: [P2][P6][R1][R2][R5][R6][S1][S2].
