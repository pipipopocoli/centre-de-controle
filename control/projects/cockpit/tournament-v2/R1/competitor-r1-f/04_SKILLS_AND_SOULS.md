# Cockpit V2 R1 - Skills and Souls Model

## Context
Locked constraints require Souls Option A and a conservative skill execution model. Variant F depends on this governance: operators only trust the vulgarisation tab if action recommendations are policy-safe and traceable.

## Problem statement
Without clear role boundaries and skill controls, the dashboard may surface unsafe actions or opaque recommendations. We need explicit assignment contracts, trust tiers, and approval gates that map directly to operator-visible risk status.

## Proposed design
### 1) Souls Option A implementation
Persistent souls:
- `@clems` (L0): strategy, policy, approvals, final arbitration.
- `@victor` (L1): reliability, quality gates, incident hardening.
- `@leo` (L1): UX clarity, docs, operator communication.

Ephemeral workers:
- Created per mission, scoped to project, time-limited.
- Must emit journal + output artifact before termination.

### 2) Skill governance lifecycle
Lifecycle states:
- `proposed -> reviewed -> approved -> active -> disabled/revoked`

Required controls:
- Pinned commit and hash for every external skill.
- Trust tier (`trusted`, `reviewed`, `untrusted`).
- Scope declaration (`workspace_only` default).
- Immutable audit event per lifecycle transition.

This aligns with supply-chain risk controls and pinned artifact practices [R4][S3].

### 3) Assignment model
Assignment contract:
`assign_skill(agent_id, skill_name, scope, expiry, rationale)`

Hard checks before assignment:
- Skill status must be `active`.
- Trust tier compatible with requested scope.
- Outside-workspace actions require @clems approval token.

### 4) Operator-visible policy cues
The Vulgarisation tab shows:
- Current approval queue count.
- Blocked actions by policy rule.
- Skill trust distribution by tier.
- Last approval actor and timestamp.

## Interfaces and contracts
### Lockfile contract
File: `control/projects/<project_id>/skills/skills.lock.json`
Required fields:
- `name`, `repo_url`, `commit_sha`, `content_hash`, `trust_tier`
- `reviewed_by`, `approved_by`, `approved_at`
- `workspace_scope`, `status`

### Audit log contract
File: `control/projects/<project_id>/skills/audit.ndjson`
Event fields:
- `event_id`, `timestamp`, `actor`, `skill_name`, `action`
- `previous_state`, `new_state`, `approval_ref`, `notes`

### Approval contract
`request_full_access(action_type, reason, scope, cost_estimate)`
- Decision values: `approved`, `denied`, `needs_info`.
- `approved` requires `approver=@clems` and expiry window.

## Failure modes
- Skill hash mismatch: block activation and log security event.
- Expired approval reused: deny execution and notify operator.
- Worker without journal output: mark run non-compliant.
- Trust tier drift after update: auto-disable until re-review.
- Hidden network behavior: quarantine skill and escalate.

## Validation strategy
- Policy simulation tests for each approval path.
- Mutation tests to verify lockfile integrity checks.
- Assignment matrix tests for all soul roles and worker roles.
- Audit completeness tests: every action must have event trail.
- Operator drills: confirm blocked/allowed actions are understandable in <=10 seconds.

## Rollout/rollback
Rollout:
1. Enforce lockfile validation on install/update.
2. Enforce assignment checks.
3. Add operator policy panel in vulgarisation tab.
4. Activate auto-quarantine on trust violations.

Rollback:
- Disable new skill installs.
- Keep existing active trusted skills only.
- Route high-risk tasks to manual execution by owner role.

## Risks and mitigations
- Risk: approval queue overload at @clems level. Mitigation: templated requests and pre-approved low-risk classes.
- Risk: too many blocked actions reduce velocity. Mitigation: tighten mission scoping and add reviewed skill inventory.
- Risk: policy status not understood by operators. Mitigation: red/yellow/green labels with plain-text reasons.

## Resource impact
- Governance overhead: moderate, mainly review and audit.
- Runtime overhead: low (hash checks and policy checks).
- Human overhead: initial review spike, then steady-state weekly maintenance.
