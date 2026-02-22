# 06_ROADMAP_40DEVS - Execution Roadmap (40-Dev Team)

## Context
This roadmap operationalizes Variant B (skills supply chain) into a 40-developer delivery program with explicit dependencies, test evidence, and risk-tagged tickets. Priority order remains stability > quality > clarity > feasibility.

## Problem statement
A plan without ticketized ownership and dependency control will not survive real delivery constraints. We need:
- Clear workstreams and owners.
- Strict DoD per ticket.
- Test evidence tied to each delivery.
- Rollout checkpoints with rollback readiness.

## Proposed design
### Work breakdown structure by workstream

Workstream WS1 - Registry and metadata core (8 devs)
- Build skill metadata schemas, versioning, and signing envelope.
- Implement registry read/write APIs and immutable history.
- Add revocation and quarantine state management.

Workstream WS2 - Policy and approvals (7 devs)
- Build PDP policy engine and PEP integration contracts.
- Implement trust-tier gates and approval workflows.
- Implement full-access `@clems` gate with audit trail.

Workstream WS3 - Resolver and lockfile pipeline (7 devs)
- Implement project resolver and lockfile writer.
- Build atomic lock update flow and merge conflict strategy.
- Add rollback pointers and canary controls.

Workstream WS4 - Runtime adapters (Codex + Antigravity) (6 devs)
- Implement policy enforcement adapter contracts.
- Ensure parity in decision traces and lock resolution.
- Add scoped sandbox enforcement.

Workstream WS5 - Eval harness and replay (6 devs)
- Build scenario packs, parity tests, replay validator.
- Add release gates and threshold governance.

Workstream WS6 - Security, ops, and operator UX (6 devs)
- Incident runbooks, dashboard contracts, and revoke drills.
- Operator comprehension checks and override governance.

Total: 40 developers.

### Milestone plan (16 weeks)
- M0 (Weeks 1-2): contracts freeze and architecture sign-off.
- M1 (Weeks 3-6): core services in shadow mode.
- M2 (Weeks 7-10): lockfile and policy soft enforcement.
- M3 (Weeks 11-13): revoke/quarantine hardening and parity gates.
- M4 (Weeks 14-16): GA readiness, incident drills, and launch checklist.

## Interfaces and contracts
Ticket contract (required fields for all tickets):
- `ticket_id`
- `owner_role`
- `dependency_ids`
- `dod`
- `test_evidence`
- `risk_level`

Cross-workstream sync contract:
- Weekly dependency resolution review.
- Daily status in `Now / Next / Blockers` format.
- Any blocker > 60 min requires two options + one recommendation.

### Ticket table

| ticket_id | owner_role | dependency_ids | dod | test_evidence | risk_level |
|---|---|---|---|---|---|
| B-001 | Staff Architect | None | Core contracts for manifest/lock/provenance approved. | API schema tests pass, design review log. | High |
| B-002 | Backend Lead | B-001 | Registry write API with immutable history shipped. | Integration tests + load test report. | High |
| B-003 | Security Lead | B-001 | Signing and key trust chain integrated with verifier. | Forged signature rejection tests. | High |
| B-004 | Backend Eng | B-002 | Revocation state model implemented. | Revoke state transition tests. | Medium |
| B-005 | Backend Eng | B-004 | Quarantine state and controls implemented. | Quarantine flow tests + audit logs. | Medium |
| B-006 | Policy Lead | B-001 | PDP baseline decision engine implemented. | Policy unit tests (allow/deny/require_approval). | High |
| B-007 | Workflow Lead | B-006 | Approval workflow for T2/T3 integrated. | Workflow e2e tests + SLA report. | Medium |
| B-008 | Platform Eng | B-006 | `@clems` full-access gate implemented. | Deny-without-approval regression tests. | High |
| B-009 | Data Eng | B-001 | Project-scoped lockfile schema finalized. | Schema validation suite. | Medium |
| B-010 | Platform Lead | B-009,B-006 | Resolver reads policy and writes atomic lock entries. | Atomicity and conflict tests. | High |
| B-011 | Tooling Eng | B-010 | Lock merge helper with signed commit metadata. | Merge conflict simulation tests. | Medium |
| B-012 | Runtime Lead | B-010,B-006 | Codex adapter enforces preflight policy checks. | Runtime conformance tests (Codex). | High |
| B-013 | Runtime Lead | B-010,B-006 | Antigravity adapter enforces identical policy checks. | Runtime conformance tests (Antigravity). | High |
| B-014 | QA Lead | B-012,B-013 | Cross-runtime parity harness implemented. | Parity score report >= target. | High |
| B-015 | QA Eng | B-003,B-010 | Integrity scenario pack v1 published. | Scenario pack run report. | Medium |
| B-016 | SRE Lead | B-004,B-012,B-013 | Revoke propagation pipeline implemented. | Revoke latency benchmark. | High |
| B-017 | SRE Eng | B-016 | Emergency freeze mode implemented and tested. | Incident drill log + rollback test. | Medium |
| B-018 | Security Ops | B-003,B-015 | Dependency confusion simulation suite added. | Red-team report. | High |
| B-019 | Security Ops | B-003 | Key rotation and compromise drill automation built. | Drill completion report. | Medium |
| B-020 | UX Lead | B-016 | Operator incident dashboard v1 shipped. | 60-second comprehension test results. | Medium |
| B-021 | Product Manager | B-020 | Override workflow with reason-code taxonomy shipped. | Audit completeness report. | Medium |
| B-022 | Compliance Lead | B-003,B-021 | Evidence retention policy approved and implemented. | Retention policy validation logs. | Medium |
| B-023 | Data Eng | B-022 | Replay bundle storage and integrity checker shipped. | Replay validation tests. | High |
| B-024 | QA Lead | B-014,B-023 | Release gate controller integrated into CI. | Gate block/pass simulation. | High |
| B-025 | PMO | B-001..B-024 | GA checklist and dependency sign-off complete. | Sign-off artifact with owner approvals. | High |
| B-026 | Perf Eng | B-010,B-014 | Install/update latency optimization pass complete. | p95 latency benchmark before/after. | Medium |
| B-027 | FinOps | B-023 | Cost dashboards and budget alerts live. | Budget alert fire drill output. | Medium |
| B-028 | Documentation Lead | B-025 | Operator runbook and rollback playbook finalized. | Runbook walkthrough pass. | Low |
| B-029 | Security Lead | B-018,B-019 | Security go/no-go review completed. | Risk acceptance memo. | High |
| B-030 | Program Director | B-025,B-029 | Launch decision completed and communicated. | Launch review minutes + checklist. | High |

Notes:
- `B-001..B-024` in dependency for B-025 means all listed tickets must be complete.
- Risk levels are delivery risk, not only security severity.

## Failure modes
- FM1: Cross-workstream dependency deadlocks.
  - Mitigation: dedicated dependency manager and weekly unblock review.

- FM2: Too many high-risk tickets in same sprint.
  - Mitigation: risk-balanced sprint planning and parallel hardening lane.

- FM3: Gate thresholds slip late in project.
  - Mitigation: freeze threshold policy at M2 unless incident-driven exception.

- FM4: Lack of test evidence for completed ticket.
  - Mitigation: ticket cannot move to Done without attached evidence artifact.

- FM5: Incident response playbooks unfinished at launch.
  - Mitigation: launch gate requires successful incident drills.

## Validation strategy
- Weekly milestone review with evidence checklist.
- Bi-weekly cross-runtime parity report.
- End-of-phase go/no-go review at M1, M2, M3, M4.
- Random audit of 10 percent completed tickets for DoD integrity.

Success signal for roadmap quality:
- 95 percent or higher tickets completed with accepted evidence on first review.
- No unresolved high-risk dependency at GA gate.

## Rollout/rollback
Rollout sequence:
1. Deliver contracts and core services in shadow mode.
2. Enable soft enforcement and gather telemetry.
3. Flip hard enforcement after gate pass.
4. Launch with incident-ready posture.

Rollback strategy:
- Revert to prior policy bundle and lock resolver release.
- Disable non-critical enforcement while keeping core integrity checks active.
- Keep revoke pipeline always enabled even in degraded mode.

## Risks and mitigations
- Risk: Hiring or staffing mismatch for 40-dev plan.
  - Mitigation: fallback staffing matrix and contractor reserve.

- Risk: Scope creep during mid-phase delivery.
  - Mitigation: strict change control and explicit scope-out register.

- Risk: Toolchain instability in CI.
  - Mitigation: isolated infra lane for harness runs.

- Risk: Security review queue delays.
  - Mitigation: pre-booked security review windows per sprint.

- Risk: Budget pressure late in project.
  - Mitigation: monthly budget reforecast and cap triggers.

## Resource impact
- Requires 40 dedicated developers plus supporting PMO, security ops, and SRE.
- CI and replay infrastructure capacity must scale with scenario volume.
- Training overhead for reviewers and operators in early milestones.
