# 02_ARCHITECTURE - Skills Supply Chain Architecture

## Context
Variant B prioritizes the integrity of skill artifacts and lifecycle controls from authoring to runtime execution. Cockpit V2 must keep Global Brain accessible for generic knowledge while preserving strict project memory isolation. The architecture therefore separates global trust metadata from project execution state.

Sources: P3, P4, D1, D2, D5, R1, R2, R3.

## Problem statement
Without a dedicated supply-chain architecture, skills may be fetched, updated, and executed through inconsistent pathways with weak auditability. This creates three critical gaps:
- Integrity gap: inability to prove artifact origin and build lineage.
- Governance gap: no deterministic gate for install/update/revoke decisions.
- Containment gap: inability to quickly quarantine compromised skills.

The design must close all three while keeping developer velocity acceptable.

## Proposed design
### A. Component model
1. Skill Registry Control Plane (global)
- Stores signed manifests, provenance refs, trust-tier metadata, and revocation state.
- Does not store project conversations or project logs.

2. Project Skill Resolver (project-scoped)
- Reads project `skills.lock`.
- Resolves exact artifact digests and approved scopes.
- Emits deterministic resolution records.

3. Policy Decision Point (PDP)
- Evaluates request context + trust tier + scope request + approval token.
- Returns `allow`, `deny`, or `allow_with_approval`.

4. Policy Enforcement Point (PEP)
- Runtime-side enforcer in Codex and Antigravity adapters.
- Blocks execution when PDP contract is not satisfied.

5. Verification service
- Verifies signatures, provenance attestations, SBOM policy, and revocation status.
- Uses local cache with strict TTL for resilience.

6. Transparency and audit stream
- Appends signed install/update/revoke decisions and execution envelopes.
- Supports deterministic replay and forensics.

7. Quarantine controller
- Moves a skill to quarantined state based on emergency signal.
- Forces deny except explicit break-glass approval path.

### B. Data flow (install)
1. Operator or agent requests install.
2. Resolver checks lockfile and requested version.
3. Verifier validates signatures/provenance/SBOM.
4. PDP evaluates policy and approval requirements.
5. If allowed, PEP records execution envelope and updates project lock.
6. Audit event is written to append-only stream.

### C. Data flow (update)
1. Update proposal compares old and new lock entries.
2. Risk delta computed (scope, maintainer keys, dependencies, CVEs).
3. Tier-dependent approval workflow triggered.
4. Canary update in selected projects.
5. Global rollout with rollback pointer kept live.

### D. Data flow (revoke)
1. Security signal (internal or external advisory).
2. Registry marks skill+digest as revoked.
3. Push revoke event to all active projects.
4. Runtimes deny future execution immediately after policy sync.
5. Existing runs are evaluated for kill or continue per risk profile.

### E. Trust tiers
- T0: local dev skill, workspace-only, no network, no persistence.
- T1: signed internal skill, workspace-only by default.
- T2: reviewed internal/external skill with provenance and SBOM checks.
- T3: critical skill, extra approvals, mandatory canary, continuous attestation verification.

ASSUMPTION (A3): Two-person review on T2/T3 remains operationally viable.

## Interfaces and contracts
### Contract 1: `SkillManifest v2`
Required fields:
- `skill_id`
- `version`
- `commit_pin`
- `artifact_digest`
- `entrypoints`
- `requested_scopes`
- `maintainer_identities`
- `trust_tier`

### Contract 2: `SkillLockEntry`
Required fields:
- `skill_id`
- `resolved_version`
- `resolved_digest`
- `commit_pin`
- `policy_bundle_id`
- `approval_id`
- `installed_at`
- `installed_by`

### Contract 3: `PolicyDecision`
Required fields:
- `decision`
- `reason_codes[]`
- `requires_approval`
- `scope_overrides`
- `ttl_seconds`

### Contract 4: `RevocationNotice`
Required fields:
- `skill_id`
- `digest`
- `revocation_reason`
- `severity`
- `issued_at`
- `effective_at`
- `issuer_signature`

### Contract 5: `RunBundle`
Required fields:
- `run_id`
- `project_id`
- `runtime_provider`
- `resolved_skill_set`
- `input_hash`
- `output_hash`
- `decision_trace`
- `event_log_hash`

### API surface (control plane)
- `POST /skills/install`
- `POST /skills/update`
- `POST /skills/revoke`
- `POST /skills/quarantine`
- `GET /skills/{id}/metadata`
- `GET /policy/bundles/{id}`
- `POST /replay/validate`

All mutating calls require signed request identity and policy checks.

## Failure modes
- FM1: Registry unavailable.
  - Effect: no fresh installs/updates.
  - Mitigation: read-only lockfile mode with cached verified artifacts.

- FM2: Verifier cache poisoning.
  - Effect: false trust decisions.
  - Mitigation: signed cache snapshots and short TTL; periodic revalidation.

- FM3: Split-brain policy bundles across regions.
  - Effect: inconsistent allow/deny decisions.
  - Mitigation: policy bundle version pin in `SkillLockEntry` and startup parity checks.

- FM4: Delayed revoke propagation.
  - Effect: compromised skill still executes.
  - Mitigation: push + pull revocation checks and max staleness SLO.

- FM5: Break-glass abuse.
  - Effect: policy bypass.
  - Mitigation: mandatory incident ticket reference and after-action audit.

- FM6: Cross-runtime behavior mismatch.
  - Effect: same lockfile different outcomes.
  - Mitigation: release gate requires conformance pass for both runtimes.

## Validation strategy
Architecture validation set:
- AV1 Contract conformance tests for all payloads.
- AV2 Signature/provenance verification tests with forged data sets.
- AV3 Revocation propagation benchmark with SLO target.
- AV4 Chaos tests: registry outage, stale cache, policy version drift.
- AV5 Replay determinism checks using `RunBundle` snapshots.
- AV6 Cross-runtime parity tests (Codex vs Antigravity).

Success criteria:
- 100 percent install/update requests produce auditable decision trace.
- Revoke-to-enforce p95 below 10 minutes (ASSUMPTION A6).
- Zero unresolved high-severity policy drift at release gate.

## Rollout/rollback
Rollout sequence:
1. Deploy architecture in shadow mode.
2. Enable signed manifest verification for new installs.
3. Introduce lockfile enforcement in canary projects.
4. Enable revoke automation and quarantine workflows.
5. Make policy parity gate release-blocking.

Rollback controls:
- Control plane rollback via immutable deployment artifact.
- Policy rollback to prior `policy_bundle_id`.
- Runtime rollback to previous resolver version with lockfile freeze.
- Incident freeze mode to stop all updates globally.

## Risks and mitigations
- Risk: Over-centralization in registry service.
  - Mitigation: multi-region read replicas and write quorum design.

- Risk: Cryptographic key lifecycle complexity.
  - Mitigation: HSM-backed keys, rotation playbooks, quarterly drills.

- Risk: Operator overload during high-volume revoke events.
  - Mitigation: severity-based automation and escalation runbook.

- Risk: External skill ecosystem inconsistency.
  - Mitigation: enforce adapter normalization and tier downgrade fallback.

- Risk: False confidence from partial provenance coverage.
  - Mitigation: policy denies missing critical attestations for T2/T3.

## Resource impact
- New services: registry metadata service, verifier, policy service, transparency writer, quarantine controller.
- Storage growth:
  - Metadata and lock history: moderate.
  - Replay bundles and audit logs: high.
- Runtime overhead:
  - Install/update path heavier due to verification and policy calls.
  - Execution path mostly unchanged except preflight checks.
- Team impact:
  - Requires dedicated security platform squad and SRE capacity for 24/7 response.
