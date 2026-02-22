# Assumptions And Validation Plan - competitor-r1-b

## Rules
- Any claim not directly proven by a cited source is tagged ASSUMPTION.
- Every ASSUMPTION includes validation owner, method, and deadline.

| assumption_id | assumption | impact_if_wrong | validation_plan | owner_role | target_phase |
|---|---|---|---|---|---|
| A1 | ASSUMPTION: 65 percent of skills can run in strict workspace-only mode without full-access exceptions. | High rework in policy and onboarding. | Run 30-day telemetry sample across top 50 skills; classify by required scope. | Platform PM | Phase 1 |
| A2 | ASSUMPTION: Lockfile verification adds less than 200 ms median install latency per skill. | UX slowdown and user bypass pressure. | Benchmark verifier in CI with 1k synthetic installs and p95 tracking. | Perf Eng | Phase 1 |
| A3 | ASSUMPTION: Two-person review on trust-tier upgrades is acceptable for velocity. | Review queue bottlenecks. | Pilot with one squad and compare lead time vs baseline. | Eng Manager | Phase 2 |
| A4 | ASSUMPTION: Sigstore-backed keyless signing is acceptable in enterprise environments. | Adoption blocked by policy/legal constraints. | Security/legal review in 3 design partners. | Security Lead | Phase 2 |
| A5 | ASSUMPTION: Replay bundles can be retained 30 days hot + 180 days cold within budget. | Budget overrun or loss of forensic depth. | Cost simulation using projected run volume and artifact sizes. | FinOps | Phase 1 |
| A6 | ASSUMPTION: 90 percent of revoke actions can complete in less than 10 minutes globally. | Incident blast radius increases. | Fire drills in staging and one canary production region. | SRE | Phase 3 |
| A7 | ASSUMPTION: Skill attestations from external maintainers can be normalized to a common schema. | Manual exceptions and policy bypass risks. | Build adapter prototypes for 5 popular ecosystems. | Supply Chain Eng | Phase 2 |
| A8 | ASSUMPTION: False-positive rate for policy deny can stay below 5 percent with staged rollout. | Developer frustration and disablement requests. | Shadow mode for 4 weeks with adjudication workflow. | Security Ops | Phase 2 |
| A9 | ASSUMPTION: Existing project memory stores can support FTS indexes without major migration downtime. | Migration delay and potential incidents. | Dry-run migration on production-like clone. | Data Eng | Phase 1 |
| A10 | ASSUMPTION: Antigravity runtime can enforce same lockfile and signature policy as Codex runtime. | Inconsistent security posture across providers. | Cross-runtime conformance tests before GA gate. | Runtime Lead | Phase 3 |
| A11 | ASSUMPTION: Workers can remain ephemeral while preserving enough evidence for audits. | Audit non-compliance. | Audit replay test with external assessor checklist. | Compliance Lead | Phase 2 |
| A12 | ASSUMPTION: Users accept mandatory risk acknowledgment when requesting full-access actions. | Approval bypass attempts. | UX A/B test in operator console. | UX Lead | Phase 2 |
