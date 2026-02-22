# 04_SKILLS_AND_SOULS - Skill Supply Chain, Trust, And Role Governance

## Context
Cockpit V2 uses Souls Option A:
- Persistent souls: `clems` (L0), `victor` (L1), `leo` (L1).
- Workers are ephemeral and project-scoped.

Variant B requires a complete skill supply chain model: skill registry, trust tiers, lockfile and commit pinning, review workflow, and lifecycle controls for install/update/revoke. Full-access actions always require `@clems` approval.

References: P2, P3, P4, P5, D1, D2, R1, R2, R3.

## Problem statement
Skills are executable units and therefore a primary attack surface. If skill sourcing and lifecycle are weak:
- A malicious update can execute quickly and spread across projects.
- Drift between reviewed source and executed artifact can go unnoticed.
- Role confusion can bypass responsibility boundaries.
- Emergency revoke may be inconsistent across runtimes.

The system must combine strict policy with practical developer flow.

## Proposed design
### A. Skill registry and trust chain
Registry stores:
- Signed `SkillManifest v2`.
- Provenance attestations.
- SBOM links.
- Trust tier and lifecycle state.
- Revocation and quarantine markers.

Every skill artifact must bind:
- `commit_pin` (source immutability),
- `artifact_digest` (binary immutability),
- `provenance_ref` (build lineage),
- `signature_chain` (identity and policy trust).

### B. Trust tiers and gate policy
- T0 Sandbox-Local:
  - Workspace-only, no external network, no persistence.
  - No promotion to shared registry.

- T1 Internal-Verified:
  - Signed by internal identity.
  - Workspace-only default.
  - Lightweight review.

- T2 Reviewed-Shared:
  - Signed + provenance + SBOM + vuln scan pass.
  - Cross-project usage allowed after review.
  - Two-person approval for scope escalation.

- T3 Critical-Core:
  - All T2 requirements plus canary rollout and continuous attestation checks.
  - Break-glass only with incident ticket and `@clems` approval.

### C. `skills.lock` contract (project-scoped)
Each lock entry:
- `skill_id`
- `resolved_version`
- `commit_pin`
- `artifact_digest`
- `trust_tier`
- `policy_bundle_id`
- `approval_id` (if required)
- `installed_at`

Policy:
- No execution if lock entry is missing or stale.
- Lockfile updates must be atomic and signed by resolver identity.

### D. Lifecycle state machine
States:
- `proposed`
- `verified`
- `approved`
- `installed`
- `active`
- `deprecated`
- `revoked`
- `quarantined`

Transitions:
1. Install path
- `proposed -> verified -> approved -> installed -> active`

2. Update path
- `active -> proposed(new) -> verified -> approved -> installed -> active`
- Keep rollback pointer to previous lock entry.

3. Revoke path
- `active -> revoked`
- Runtime denies future starts.

4. Quarantine path
- `active -> quarantined`
- Stronger than revoked for incident triage; allows forensic replay only.

### E. Review workflow
- Step 1: automated checks (schema/signature/provenance/SBOM/vuln).
- Step 2: policy review by owning role.
- Step 3: trust-tier gate:
  - T0/T1: single reviewer.
  - T2/T3: dual reviewer + security sign-off.
- Step 4: publish decision with immutable audit event.

### F. Souls responsibility model
- `@clems`:
  - Approves full-access actions.
  - Final approver for trust-tier escalation to T3.
  - Final gate for global promotions and emergency overrides.

- `@victor`:
  - Owns execution reliability and rollback readiness.
  - Operates incident response for revoke and quarantine.

- `@leo`:
  - Owns quality, testing strategy, policy conformance reports.
  - Maintains non-regression thresholds.

- `@agent-N` workers:
  - Execute bounded project tasks.
  - Cannot self-upgrade trust tier.
  - Must emit run bundle evidence.

ASSUMPTION (A11): Ephemeral workers plus run bundle retention satisfy audits.

## Interfaces and contracts
### Contract: `InstallRequest`
- `project_id`
- `skill_id`
- `requested_version`
- `requested_scopes`
- `requester_role`
- `approval_token` (optional, required when policy says so)

### Contract: `InstallDecision`
- `decision` (`allow`, `deny`, `require_approval`)
- `reason_codes`
- `lock_entry_preview`
- `expires_at`

### Contract: `UpdateProposal`
- `old_lock_entry`
- `new_manifest_ref`
- `risk_delta`
- `required_reviewers`
- `canary_plan`

### Contract: `RevokeAction`
- `skill_id`
- `digest`
- `severity`
- `effective_at`
- `kill_running_jobs` (bool)
- `issuer`

### Contract: `ScopePolicy`
- `workspace_read`
- `workspace_write`
- `network_access`
- `external_fs_access`
- `tool_allowlist`

Policy rule:
- `external_fs_access=true` implies `@clems` approval.

## Failure modes
- FM1: Compromised maintainer key signs malicious update.
  - Mitigation: threshold trust and delegated roles (P3, D2), plus forced key rotation.

- FM2: Dependency confusion via namespace collision.
  - Mitigation: registry allowlist + explicit namespace ownership + pinned source refs.

- FM3: Provenance present but forged or unverifiable.
  - Mitigation: verifier requires trusted identity roots; deny unverifiable attestations.

- FM4: Revoked skill still runs due to stale policy cache.
  - Mitigation: short cache TTL, periodic pull check, emergency push invalidation.

- FM5: Review fatigue causes weak approvals.
  - Mitigation: risk-based routing and required evidence checklist.

- FM6: Cross-runtime policy mismatch.
  - Mitigation: parity test gate blocks release.

- FM7: Break-glass used for convenience.
  - Mitigation: require incident ID and post-mortem action item.

## Validation strategy
Validation layers:
- VL1 Supply chain integrity tests:
  - tampered manifest
  - mismatched digest
  - bad signature chain

- VL2 Lifecycle tests:
  - install/update/revoke/quarantine transitions
  - invalid transition denial

- VL3 Policy tests:
  - full-access request without `@clems` approval must deny
  - scope escalation requires expected approvals

- VL4 Attack simulation:
  - dependency confusion
  - compromised signer key
  - stale revocation cache

- VL5 Human workflow tests:
  - dual-review SLA
  - override audit completeness

Release gate:
- No open high-severity finding in VL1-VL4.
- 100 percent of overrides linked to incident references.

## Rollout/rollback
Rollout:
1. Introduce lockfile generation and verification in advisory mode.
2. Enforce lockfile and pin for new installs.
3. Enable update workflow with risk delta and canary.
4. Enable revoke and quarantine automation.
5. Turn on strict enforcement for all tiers.

Rollback:
- Revert policy bundle to last known-good version.
- Freeze updates and keep currently locked versions active.
- Disable risky tier transitions until incident review closes.

## Risks and mitigations
- Risk: T2/T3 review throughput bottleneck.
  - Mitigation: reviewer pool and SLA dashboards.

- Risk: External ecosystems provide incomplete metadata.
  - Mitigation: adapter normalization and tier downgrade fallback.

- Risk: Lockfile conflicts in high-velocity projects.
  - Mitigation: lockfile merge bot with conflict policy and reviewer check.

- Risk: Overly strict policy hurts productivity.
  - Mitigation: shadow mode metrics before hard enforcement (A8).

- Risk: Signature infra dependency outage.
  - Mitigation: cached trusted snapshots and degraded read-only mode.

### Attack surface analysis and containment policy
Attack surfaces:
1. Source repository compromise.
2. CI builder compromise.
3. Registry metadata tampering.
4. Dependency namespace hijack.
5. Runtime policy bypass.
6. Human override abuse.

Containment policy:
- Immediate revoke for confirmed compromised digests.
- Quarantine for suspected compromise pending triage.
- Blast-radius query by project and runtime provider.
- Forced lock refresh on all active projects.
- Mandatory post-incident policy patch before restore.

References: P2, P4, P5, D1, D2, R3, R5.

## Resource impact
- Security engineering:
  - Additional staffing for trust-tier review and incident response.
- Platform engineering:
  - Resolver, policy, and verifier integration work.
- Developer workflow:
  - More explicit approvals for high-risk operations.
- Runtime:
  - Additional preflight checks before skill execution.
