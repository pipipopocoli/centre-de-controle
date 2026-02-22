# 04_SKILLS_AND_SOULS - Execution model with memory controls

## Context
Souls Option A is fixed: persistent clems/victor/leo and ephemeral workers. Skills are executable but workspace-scoped by default. Memory policies must align with these constraints.

## Problem statement
If skills can read/write memory without role-aware policy, workers can accidentally leak or import project-specific state into wrong contexts.

## Proposed design
### Role matrix
- clems (L0)
  - approve Global Brain promotion and full-access actions.
  - can revoke promotion artifacts.
- victor (L1)
  - manage backend memory policies within workspace limits.
- leo (L1)
  - manage UX/vulgarisation memory presentation and operator clarity.
- worker (ephemeral)
  - task-scoped access only, no promotion rights.

### Skill execution scopes
- default scope: workspace-only read/write.
- restricted scope: read-only retrieval for assigned project.
- elevated scope: requires @clems approval token.

### Souls-memory contracts
- Every soul action attaches:
  - actor_id
  - role_level
  - project_id
  - skill_id
  - approval_token(optional)
  - memory_scope
- Worker session expiration forces memory handle revocation.

## Interfaces and contracts
- SkillExecutionRequest
  - actor_id
  - role_level
  - project_id
  - scope_request
  - task_id
- SkillExecutionGrant
  - granted_scope
  - ttl
  - approval_ref
- PromotionApproval
  - candidate_ref
  - approved_by=@clems
  - rationale
  - revoke_path

## Failure modes
- FM-SKILL-1: worker obtains stale elevated token.
- FM-SKILL-2: skill reads from non-target project.
- FM-SKILL-3: promotion created without explicit approver identity.

## Validation strategy
- Policy engine tests for role and scope combinations.
- Token TTL expiration tests.
- Negative tests for cross-project retrieval attempts.
- Audit tests that every elevated action has approval_ref.

## Rollout/rollback
- Rollout
  - enforce scope contract in dry-run mode first.
  - switch to blocking mode after false-positive review.
- Rollback
  - fail-open only for read paths with warning.
  - keep write/promotion fail-closed.

## Risks and mitigations
- Risk: strict policy blocks valid workflows.
  - Mitigation: allowlist exception process with expiry and review.
- Risk: approval latency slows progress.
  - Mitigation: batchable approval packets and SLA target.

## Resource impact
- Policy engine and audit lane requires dedicated 4-dev subteam.
- Additional logs for access events increase storage modestly.

## Evidence tags used
[P4][P8][R6][S2][S3][ASSUMPTION-A1]
