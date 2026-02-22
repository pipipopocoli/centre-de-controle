# 06 - Roadmap 40 Devs (Eval harness first)

## Context
Cockpit V2 planning must be execution-ready for a team of roughly 40 developers. Variant E requires explicit non-regression machinery with release gates and evidence loops.

## Problem statement
Large teams drift when workstreams are not clearly split and ticket dependencies are implicit. We need a roadmap that is small-batch, testable, and reversible.

## Proposed design
## Work breakdown structure by workstream
- WS1 Eval Control Plane
  - scenario registry
  - scheduler
  - gate engine
  - report service
- WS2 Replay and Artifacts
  - deterministic bundle format
  - hermetic runners
  - artifact retention and hashing
- WS3 Metrics and Observability
  - metrics schema + dashboards
  - confusion matrix computation
  - SLOs and alerts
- WS4 Policy and Approvals
  - override workflow
  - audit trail
  - approval enforcement in CI
- WS5 Memory and Contamination Guardrails
  - isolated indexing
  - promotion workflow
  - compaction and retention policy
- WS6 Developer Experience and UI
  - operator panel
  - failure triage UX
  - vulgarisation summaries
- WS7 Reliability and Cost Engineering
  - autoscaling/sharding
  - runtime and budget guardrails
  - rollback automation

## Interfaces and contracts
- All tickets must define contract tests and evidence outputs.
- Every merge candidate must emit replay artifact hashes.
- Release blockers are controlled only by gate verdict contract.

## Failure modes
- Dependency deadlocks across workstreams.
- Too many concurrent initiatives break WIP discipline.
- Ticket DoD too vague to verify.

## Validation strategy
- Weekly program review on dependency critical path.
- SLA checks on ticket aging and blocker resolution.
- Random audit of completed tickets for evidence quality.

## Rollout/rollback
- Rollout in 4 program increments of 2 weeks each.
- Each increment ends with rollback drill on latest gate changes.

## Risks and mitigations
- Risk: coordination overhead at 40-dev size.
  - Mitigation: strict owner model and small reversible PRs.
- Risk: delayed value due to over-architecture.
  - Mitigation: enforce MVP gates by week 4.

## Resource impact
- Program staffing:
  - 6 platform infra,
  - 8 quality/reliability,
  - 10 runtime/orchestration,
  - 8 product/frontend,
  - 8 shared feature teams.

## Ticket table
| ticket_id | owner_role | dependency_ids | dod | test_evidence | risk_level |
|---|---|---|---|---|---|
| EVAL-001 | platform-lead | - | Scenario registry v1 in prod-like env | API contract tests + sample registry diff | Medium |
| EVAL-002 | qa-lead | EVAL-001 | B0/B1 suites defined and versioned | Suite manifest checks + dry-run logs | Medium |
| EVAL-003 | infra-lead | EVAL-002 | Scheduler supports shard + retry policy | Load test report + queue latency graph | High |
| EVAL-004 | runtime-lead | EVAL-002 | Hermetic runner image with env.lock verification | Reproducibility pass on seed matrix | High |
| EVAL-005 | data-lead | EVAL-003,EVAL-004 | Artifact store immutable writes + hash index | Integrity check logs + tamper test | High |
| EVAL-006 | metrics-lead | EVAL-003 | Metrics schema (`metrics.json`) adopted | Schema conformance tests + sample outputs | Medium |
| EVAL-007 | policy-lead | EVAL-006 | Gate engine hard/soft policy v1 | Policy unit tests + synthetic runs | High |
| EVAL-008 | policy-lead | EVAL-007 | Override workflow requires @clems reference | Approval contract test + audit entry proof | High |
| EVAL-009 | sre-lead | EVAL-003,EVAL-007 | Alerting + SLOs for gate availability | Alert fire drill logs + dashboard snapshot | Medium |
| EVAL-010 | qa-lead | EVAL-006,EVAL-007 | FP/FN measurement pipeline live | Confusion matrix report + calibration notes | High |
| EVAL-011 | memory-lead | EVAL-005 | Project-isolated index with deny-by-default cross-project reads | Isolation tests + denial logs | High |
| EVAL-012 | memory-lead | EVAL-011 | Promotion API to Global Brain behind approval | Promotion audit report + policy checks | Medium |
| EVAL-013 | ui-lead | EVAL-007,EVAL-010 | Operator dashboard with PASS/SOFT/HARD clarity | UX acceptance session + screenshot evidence | Medium |
| EVAL-014 | ux-writer | EVAL-013 | 60-second vulgarisation panel integrated | Timed comprehension test logs | Low |
| EVAL-015 | release-lead | EVAL-008,EVAL-010 | Release packet generator v1 | Generated packet from staging run | Medium |
| EVAL-016 | cost-lead | EVAL-003,EVAL-006 | Runtime and token budget guardrails | Budget threshold tests + weekly cost report | Medium |
| EVAL-017 | sec-lead | EVAL-005,EVAL-008 | Audit log tamper-evidence and retention policy | Security test report + checksum validation | High |
| EVAL-018 | program-lead | EVAL-001..EVAL-017 | End-to-end rehearsal complete | E2E runbook + rollback drill log | High |
| EVAL-019 | qa-lead | EVAL-018 | 90-day benchmark governance process active | Governance doc + first monthly review | Medium |
| EVAL-020 | product-owner | EVAL-018,EVAL-019 | Go-live decision with signed risk acceptance | Decision record in DECISIONS.md | High |
