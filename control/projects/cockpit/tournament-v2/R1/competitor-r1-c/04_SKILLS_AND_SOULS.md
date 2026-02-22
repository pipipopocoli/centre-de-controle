# 04_SKILLS_AND_SOULS - Operating Model

## Context
- Souls and skills determine who can execute what in the orchestration graph.
- Variant C requires explicit role and permission contracts to keep router decisions safe.

## Problem statement
- Without strict assignment and approval boundaries, the router can dispatch unsafe tool calls or off-mission actions.
- Skills supply chain and runtime scope must remain auditable and workspace-first.

## Proposed design
### 1) Souls model (Option A)
- Persistent:
  - clems (L0): global policy, approvals, conflict resolution.
  - victor (L1): architecture reliability, gates, incident response.
  - leo (L1): UX, vulgarisation, operator communication.
- Workers:
  - ephemeral, mission-scoped, explicit owner and expiry.

### 2) Skill execution scope
- Default: workspace-only read/write.
- Elevated access requires @clems approval for:
  - outside workspace read/write
  - deep folder surgery
  - external skill install/update
  - off-mission activities
  - API spend beyond baseline assumptions

### 3) Assignment policy
- `assign_skill(agent_id, skill_id, scope, expiry, rationale, owner)`
- Constraints:
  - skill must be active and pinned.
  - trust tier not untrusted for production use.
  - assignment must include fallback behavior.

### 4) Runtime guardrails
- PolicyEngine validates each tool action against:
  - project lock
  - skill scope
  - role permissions
  - approval refs
- Router rejects dispatch on guardrail failure.

## Interfaces and contracts
### Skill registry contract
- Fields:
  - `skill_id`
  - `repo_url`
  - `commit_sha`
  - `trust_tier`
  - `status`
  - `approved_by`
  - `workspace_scope`

### Soul state contract
- Fields:
  - `soul_id`
  - `role`
  - `active_missions[]`
  - `approval_authority`
  - `heartbeat`

### Permission matrix contract
- Dimensions:
  - role x action x scope x approval_required

## Failure modes
- FM-SS-01: worker assigned broad scope unintentionally.
- FM-SS-02: skill update drifts from pinned commit.
- FM-SS-03: missing fallback leads to stalled mission.
- FM-SS-04: approval reference omitted in elevated action.

## Validation strategy
- Assignment lint check for missing expiry/owner/fallback.
- Lockfile hash check before and after update.
- Policy replay tests with denied elevated actions.
- Approval audit tests for elevated action set.

## Rollout/rollback
- Rollout:
  - enable registry checks first.
  - enforce assignment contract.
  - enforce elevated-action approval gate.
- Rollback:
  - disable non-essential skills.
  - freeze updates and revert to last known lockfile.

## Risks and mitigations
- Risk: assignment overhead slows urgent response.
  - Mitigation: predefined emergency templates with strict expiry.
- Risk: trust tier misclassification.
  - Mitigation: dual review for tier changes.

## Resource impact
- Team:
  - 4 devs policy engine integration
  - 3 devs registry and lockfile automation
  - 2 devs audit reporting
- Ops:
  - low runtime overhead, medium governance overhead.

## Source pointers
- SRC-D3,SRC-R6,SRC-R7.
- Assumptions: ASSUMPTION-A1, ASSUMPTION-A6.
