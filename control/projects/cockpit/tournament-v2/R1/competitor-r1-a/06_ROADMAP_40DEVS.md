# 06_ROADMAP_40DEVS

## Context
This roadmap converts the stability-first architecture into a 40-dev execution model with explicit ownership, dependencies, and proof-based DoD.

## Problem statement
Large teams fail when roadmap items are vague, unticketed, or missing clear dependency and evidence rules.

## Proposed design
Roadmap horizon: 16 weeks.

Workstreams:
- WS1 Platform Persistence Core
- WS2 Replay and Recovery
- WS3 Memory Isolation and Promotion
- WS4 Policy and Approval Gates
- WS5 Skills and Souls Runtime
- WS6 Eval Harness and Release Gates
- WS7 Operator and Reporting Layer

Phases:
- Phase 1 (Weeks 1-4): contracts and shadow mode.
- Phase 2 (Weeks 5-8): dual write and replay validation.
- Phase 3 (Weeks 9-12): pilot rollout with hard gates.
- Phase 4 (Weeks 13-16): scale rollout and operational hardening.

## Interfaces and contracts
Ticket contract fields:
- ticket_id
- owner_role
- dependency_ids
- dod
- test_evidence
- risk_level

Dependency policy:
- no ticket starts without declared dependency status.
- high-risk tickets require rollback procedure before merge.

## Failure modes
- FM1: dependency deadlock between workstreams.
- FM2: overloaded critical owner roles.
- FM3: release pressure bypassing DoD evidence.

## Validation strategy
- Weekly dependency graph review.
- WIP caps by workstream.
- DoD evidence audit at phase gates.

## Rollout/rollback
- Rollout by phase gates only.
- Rollback at workstream scope if gate fails.

## Risks and mitigations
- Risk: parallelism creates hidden integration debt.
  - Mitigation: integration scrum and nightly compatibility checks.
- Risk: insufficient reliability staffing.
  - Mitigation: reserve 25 percent of capacity for reliability tasks.

## Resource impact
- 40 dev allocation:
  - WS1: 8
  - WS2: 7
  - WS3: 6
  - WS4: 5
  - WS5: 5
  - WS6: 6
  - WS7: 3

## Work breakdown structure by workstream
- WS1
  - define WAL and commit contracts
  - implement idempotency and sequence guards
  - add persistence observability
- WS2
  - build replay engine
  - build rollback operator tools
  - add crash recovery drills
- WS3
  - lock project memory boundaries
  - add promotion queue and approval path
  - add compaction and retention lanes
- WS4
  - policy middleware and approval APIs
  - audit trail integrity checks
  - fail-closed behavior tests
- WS5
  - souls and worker lifecycle controls
  - skill execution scope enforcement
  - skill version pinning
- WS6
  - deterministic replay suites
  - corruption/chaos tests
  - release gate automation
- WS7
  - operator incident dashboards
  - status reporting
  - handoff templates

## Ticket table
| ticket_id | owner_role | dependency_ids | dod | test_evidence | risk_level |
|---|---|---|---|---|---|
| TKT-001 | platform_lead | none | WAL contract doc merged | contract review pass | medium |
| TKT-002 | platform_eng | TKT-001 | append-only store prototype | replay smoke pass | high |
| TKT-003 | platform_eng | TKT-002 | idempotent commit path | duplicate write test | high |
| TKT-004 | sre | TKT-002 | checksum and corruption alarms | mutation test pass | high |
| TKT-005 | reliability_lead | TKT-003 | retry state machine spec | state transition tests | medium |
| TKT-006 | reliability_eng | TKT-005 | backoff implementation | timeout chaos pass | medium |
| TKT-007 | replay_lead | TKT-003 | run bundle schema v1 | schema validation pass | high |
| TKT-008 | replay_eng | TKT-007 | replay engine mvp | deterministic hash pass | high |
| TKT-009 | replay_eng | TKT-008 | rollback executor | rollback drill pass | high |
| TKT-010 | memory_lead | none | memory isolation policy | policy unit tests | high |
| TKT-011 | memory_eng | TKT-010 | project FTS baseline | isolation query tests | medium |
| TKT-012 | memory_eng | TKT-011 | compaction scheduler | compaction replay pass | medium |
| TKT-013 | policy_lead | none | approval API contract | API conformance pass | high |
| TKT-014 | policy_eng | TKT-013 | full-access gate middleware | bypass test blocked | high |
| TKT-015 | policy_eng | TKT-014 | immutable audit events | tamper detection pass | high |
| TKT-016 | runtime_lead | none | souls option A lifecycle spec | role test pass | medium |
| TKT-017 | runtime_eng | TKT-016 | worker ttl enforcement | ttl expiry tests | medium |
| TKT-018 | runtime_eng | TKT-017 | workspace-only skill scope | scope violation test | high |
| TKT-019 | runtime_eng | TKT-018 | skill version pinning | replay compatibility pass | medium |
| TKT-020 | eval_lead | TKT-008 | replay regression suite | suite baseline pass | high |
| TKT-021 | eval_eng | TKT-020 | crash injection suite | crash matrix pass | high |
| TKT-022 | eval_eng | TKT-021 | corruption suite | checksum quarantine pass | high |
| TKT-023 | eval_eng | TKT-020 | policy conformance suite | bypass incidents zero | high |
| TKT-024 | release_lead | TKT-020,TKT-021,TKT-022,TKT-023 | release gate automation | dry run gate pass | high |
| TKT-025 | sre | TKT-024 | rollback runbook | game day pass | medium |
| TKT-026 | ui_lead | TKT-024 | incident dashboard v1 | operator drill pass | medium |
| TKT-027 | ui_eng | TKT-026 | run status timeline | timeline replay match | low |
| TKT-028 | docs_lead | TKT-024 | operator handbook | review signoff | low |
| TKT-029 | pm | TKT-001..TKT-028 | phase gate checklist | checklist audit pass | medium |
| TKT-030 | clems_delegate | TKT-029 | promotion governance packet | approval workflow pass | medium |

Evidence tags used: [P2][P6][P7][P8][R1][R2][R3][R6][S1][S2].
