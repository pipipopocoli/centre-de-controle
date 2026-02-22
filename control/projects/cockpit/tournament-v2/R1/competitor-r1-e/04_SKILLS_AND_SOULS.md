# 04 - Skills and Souls (Policy-safe execution)

## Context
Locked constraints define Souls Option A:
- persistent souls: `@clems` (L0), `@victor` (L1), `@leo` (L1),
- workers are ephemeral and project-scoped,
- skills executable in V2, default workspace-only,
- full access actions require `@clems` approval.

## Problem statement
Eval harness execution spans many tasks (benchmark prep, replay, adjudication). Without clear soul/worker boundaries and skill policy, responsibility and safety degrade quickly.

## Proposed design
### Responsibility matrix
- `@clems`:
  - policy authority, hard-fail override, promotion approval.
- `@victor`:
  - architecture integrity, risk triage, gate policy evolution.
- `@leo`:
  - execution quality, roadmap/tickets, delivery cadence.
- `@agent-n` workers:
  - bounded subtasks, no persistent authority, strict mission scope.

### Skill execution policy
- Tier 0 skills (safe local): read/write inside workspace.
- Tier 1 skills (guarded): network read or expensive compute.
- Tier 2 skills (restricted): outside workspace access, major install/update.

Rules:
- Tier 2 always needs explicit `@clems` approval.
- Skill lock metadata stores: source repo, pinned commit, reviewer, expiry.
- Every skill run emits trace events for eval harness audit.

### Eval-specific worker pattern
- `worker-eval-runner`: executes assigned replay shards.
- `worker-eval-triage`: classifies fail type (bug, flake, infra, policy).
- `worker-eval-reporter`: drafts evidence packet and remediation notes.

## Interfaces and contracts
- Worker mission contract:
  - `{mission_id, objective, constraints, expected_output, timeout}`.
- Skill run contract:
  - `{skill_id, tier, scope, project_id, approval_ref, result_hash}`.
- Accountability contract:
  - every gate-impacting action maps to single owner role.

## Failure modes
- Role ambiguity between victor and leo.
- Worker scope creep beyond assigned mission.
- Skill supply chain drift (unpinned updates).
- Missing approval records for restricted actions.

## Validation strategy
- Quarterly role fire-drill with synthetic incidents.
- Automated policy checks on skill metadata.
- Mission contract linting before worker dispatch.
- Audit sampling of override decisions and approvals.

## Rollout/rollback
- Rollout:
  - enforce mission templates,
  - enforce skill tier tags,
  - enforce approval references in CI.
- Rollback:
  - disable restricted skill categories,
  - route critical flows to manual lead review.

## Risks and mitigations
- Risk: too much governance slows delivery.
  - Mitigation: pre-approved safe lane for Tier 0 repetitive tasks.
- Risk: invisible delegation quality issues.
  - Mitigation: mandatory Now/Next/Blockers and artifact proofs.
- Risk: inconsistent policy enforcement.
  - Mitigation: automated contract checks before merge.

## Resource impact
- Additional governance overhead: ~5 to 8 percent process time.
- Fewer incidents from unsafe actions offsets cost.
- Better traceability lowers triage MTTR.

## References
Key sources: [R1][R5][R7][S2][S3], assumptions [A1][A3].
