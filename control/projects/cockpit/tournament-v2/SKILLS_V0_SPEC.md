# SKILLS V0 SPEC - Install, trust, assignment, approvals

## 0) Purpose
- Define auditable workflow for external skill sourcing and execution in Cockpit V2.
- Keep default safety posture workspace-only.

## 1) Core principles
- No unpinned external skill install.
- No automatic updates.
- No full access by default.
- Every install/update/revoke must leave audit trace.

## 2) Skill source proposal contract
Every new skill proposal must include:
- skill_name
- source_repo_url
- pinned_commit_sha
- rationale
- expected_scope
- expected_risk
- owner_role

Optional but recommended:
- source_tag
- source_hash
- changelog_link

## 3) Trust tiers
- trusted:
  - first-party or organization-controlled source
  - faster approval path, still pinned
- reviewed:
  - external source, audited by team
  - install allowed after review checklist + approval
- untrusted:
  - sandbox-only evaluation
  - no production assignment

## 4) Lockfile contract (mandatory)
Store lock entries per skill with fields:
- name
- repo_url
- commit_sha
- content_hash
- trust_tier
- reviewed_by
- approved_by
- approved_at
- workspace_scope
- status (active/disabled/revoked)

Recommended location:
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/skills/skills.lock.json`

## 5) Install workflow
1. Propose skill with required metadata.
2. Verify source and pin commit SHA.
3. Classify trust tier.
4. Run review checklist:
   - execution surface
   - data access scope
   - network behavior
   - side effects
5. Request @clems approval.
6. Record lockfile entry.
7. Install in workspace-only mode.
8. Run smoke check.

## 6) Update workflow
- Allowed only when:
  - new commit SHA is pinned
  - diff reviewed
  - @clems approval recorded
- Update steps:
  - clone/check new pinned commit
  - security review delta
  - update lockfile entry
  - test on sandbox workspace
  - promote to active

## 7) Revoke workflow
Trigger conditions:
- vulnerability found
- unexpected behavior
- policy violation
- no longer needed

Revoke steps:
- mark status `revoked` in lockfile
- remove runtime assignment
- keep audit trail
- attach incident note

## 8) Default permission matrix
- workspace-only (default):
  - read/write inside active project workspace only
- elevated (approval required):
  - outside workspace read/write
  - deep refactor automation
  - external publishing operations
  - billable API operations beyond baseline

## 9) Assignment model by @clems
Role-based baseline:
- clems (L0): orchestration, policy, approval-sensitive skills
- victor (L1): reliability, testing, gatekeeping, infra controls
- leo (L1): UX, docs, vulgarisation, operator communication
- workers: narrow task skills, ephemeral assignment

Assignment protocol:
- assign_skill(agent_id, skill_name, scope, expiry, rationale)
- verify trust tier and lockfile status before assign
- deny if status not active

## 10) Guardrails
- no unpinned install
- no auto-update
- no hidden network access
- no approval bypass
- no unknown binaries in active path

## 11) Audit trail requirements
For each skill lifecycle event log:
- event_id
- timestamp
- actor
- project_id
- skill_name
- action (propose/install/update/revoke/assign/unassign)
- previous_state
- new_state
- approval_ref
- notes

## 12) Failure handling
- If pin or hash mismatch:
  - block install/update
  - log security event
- If runtime behavior deviates from declared scope:
  - disable skill
  - escalate to @clems
  - require re-review before reuse
