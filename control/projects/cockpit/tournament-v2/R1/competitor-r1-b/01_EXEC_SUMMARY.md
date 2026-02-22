# 01_EXEC_SUMMARY - Cockpit V2 R1 Variant B (Skills Supply Chain)

## Context
Cockpit V2 needs a secure, fast, and auditable way to execute skills while preserving strict project isolation and keeping Global Brain available for generic knowledge. The axis for this variant is the skill supply chain: registry trust, install/update/revoke controls, lockfile policy, and attack containment. This package is plan-only and does not change runtime code.

References: P2, P3, P4, P5, D1, D2.

## Problem statement
Current and expected risks in skill execution pipelines are:
- Untrusted or weakly verified skill artifacts can be installed and executed (supply chain poisoning).
- Drift between declared and executed dependency versions can bypass reviews.
- Emergency revocation is often slow, causing large blast radius.
- Multi-provider execution (Codex and Antigravity) can create policy asymmetry.
- Operator decisions under pressure can skip required review depth.

If unresolved, the platform can fail on stability, security, and compliance. Historical attack studies on package ecosystems validate this risk class (P2, P5).

## Proposed design
Decision summary:
- Build a 3-layer skill supply chain model:
  1. Trust and provenance layer: signing, attestations, transparency, verifier.
  2. Control layer: policy engine, approvals, lifecycle state machine.
  3. Runtime layer: workspace-scoped execution sandbox + deterministic run bundle.
- Enforce `skills.lock` with pin-commit, digest, provenance references, and risk tier.
- Introduce trust tiers T0-T3 with explicit upgrade gates.
- Define lifecycle contracts for install, update, revoke, quarantine, recover.
- Add cross-runtime conformance suite so Codex and Antigravity must pass identical policy checks before promotion.

Expected outcome:
- Faster containment during incidents.
- Higher integrity of executed skills.
- Clear operator accountability and replay evidence.

References: P3, P4, P8, D1, D2, R1, R2, R3.

## Interfaces and contracts
Core contracts proposed:
- `SkillManifest v2`: name, version, commit_pin, artifact_digest, requested_scopes, maintainer_keys.
- `SkillProvenance v1`: builder_identity, source_uri, source_digest, build_steps, timestamp, signature_chain.
- `skills.lock`: project-level immutable lock entries with trust_tier and approval_id.
- `SkillPolicyDecision`: allow, deny, allow_with_approval, plus reason codes.
- `RunBundle`: deterministic event stream, inputs hash, resolved skills, outputs hash, policy decision trace.

Approval contract:
- Full-access actions require `@clems` approval token before execution.

References: D1, D2, D5, R3.

## Failure modes
Top failure modes:
- FM1: Signature verification outage blocks installs.
- FM2: Revocation propagation lag leaves compromised skill active.
- FM3: Lockfile merge conflicts cause unintended downgrade/upgrade.
- FM4: Policy engine mismatch between Codex and Antigravity.
- FM5: False-positive policy denies push teams to bypass path.

Each failure mode is mapped to test gates in `05_EVAL_HARNESS.md` and incident runbooks in roadmap tickets.

## Validation strategy
Validation stack:
- Static checks: manifest schema, lockfile integrity, policy lint.
- Dynamic checks: install/update/revoke simulation, replay determinism, chaos tests.
- Security checks: key rotation drills, forged provenance tests, dependency confusion simulations.
- Cross-runtime checks: same input -> same policy decision -> same lock resolution.
- Operator checks: 60-second comprehension task for incident dashboards.

Evidence and assumptions are tracked in:
- `EVIDENCE/01_SOURCES.md`
- `EVIDENCE/02_ASSUMPTIONS.md`
- `EVIDENCE/03_CLAIM_TRACE.md`

## Rollout/rollback
Rollout:
1. Phase 0: Observe-only verifier and lockfile checker.
2. Phase 1: Soft enforcement for new installs.
3. Phase 2: Full enforcement for updates + revoke pipeline.
4. Phase 3: Runtime parity gate for Codex and Antigravity.
5. Phase 4: GA with audited incident drill success.

Rollback:
- Policy rollback by versioned bundle (`policy_bundle_id`).
- Registry rollback by channel pin (`stable`, `candidate`, `frozen`).
- Emergency freeze mode: deny new skill installs except allowlist.

## Risks and mitigations
- Risk: Review queue overload on trust-tier changes.
  - Mitigation: staged delegation with two-person rule only for T2/T3.
- Risk: Latency overhead from heavy verification.
  - Mitigation: cache validated attestations + parallel prefetch.
- Risk: Vendor/provider policy drift.
  - Mitigation: cross-runtime conformance gate is release-blocking.
- Risk: Human override misuse.
  - Mitigation: mandatory reason code + post-incident review.
- Risk: Cost growth for retention and replay bundles.
  - Mitigation: hot/cold retention split and weekly cost guardrail.

Assumptions requiring validation: A1, A2, A3, A5, A10, A12.

## Resource impact
- Team: 40-dev program, 6 workstreams, 16-week initial delivery, then hardening.
- Infra: metadata store, transparency backend, policy service, replay storage.
- Runtime: estimated +4 to +9 percent install path overhead before optimization.
- Ops: 24/7 on-call coverage needed for revoke and incident management.
- Budget envelope and staffing model in `07_RESOURCE_BUDGET.md`.
