# Cockpit V2 R1 - Roadmap for 40-dev Team

## Context
This roadmap converts the Variant F plan into a ticketized execution program for a 40-dev organization. It keeps delivery small, testable, and reversible while preserving strict policy boundaries.

## Problem statement
Without explicit workstream ownership and dependency mapping, a 40-dev effort quickly stalls in integration debt. We need a concrete sequence that delivers operator clarity, reliability, and governance in parallel.

## Proposed design
### Delivery horizon
- Total: 12 weeks
- Cadence: 2-week increments, weekly integration train
- Rollout path: Shadow -> Assisted -> Default -> Hard Gate

### Work breakdown structure by workstream
| workstream_id | scope | squad_size | owner_role | key outputs |
|---|---|---:|---|---|
| WS1 | UX information architecture and pressure-mode layout | 6 | frontend_lead | Dashboard IA, visual hierarchy, card contracts |
| WS2 | Data ingestion and snapshot contracts | 7 | backend_lead | Adapters, schema validation, canonical snapshot |
| WS3 | Orchestrator and durable run bundles | 5 | reliability_lead | State machine, retries, replay artifacts |
| WS4 | Memory stack (FTS, compaction, optional semantic pilot) | 5 | data_lead | Indexed memory, digest jobs, promotion queue |
| WS5 | Skills and policy gate integration | 4 | security_lead | Lockfile checks, approval APIs, audit events |
| WS6 | Eval harness and regression gates | 5 | qa_lead | Scenario packs, gate engine, reports |
| WS7 | Observability and cost telemetry | 4 | sre_lead | Metrics, alerts, budget dashboards |
| WS8 | Docs, operator runbook, enablement | 4 | docs_lead | Playbooks, training kit, rollout checklist |

### Milestone plan
- M1 (Week 2): Contracts frozen, baseline snapshot and static dashboard.
- M2 (Week 4): Deterministic run bundle + replay in CI.
- M3 (Week 6): Policy gate wired, skill trust panel live.
- M4 (Week 8): Eval harness soft gate active.
- M5 (Week 10): Pilot operators on assisted mode.
- M6 (Week 12): Hard gates active for pilot cohort.

## Interfaces and contracts
Program-level contracts:
- Every ticket references a single owner role.
- Every merge includes test evidence entry.
- No full-access workflow without approval API integration.
- Every milestone requires rollback procedure ready.

Release contract:
- Build is releasable only if WS2, WS3, WS5, and WS6 gates pass together.

## Failure modes
- Dependency gridlock: too many blocked tickets waiting on contracts.
- Integration train misses: parallel streams diverge on schema.
- Quality debt: UX polish progresses faster than deterministic backend.
- Policy debt: features shipped before approval gates are enforced.

## Validation strategy
- Weekly dependency review with critical path updates.
- Daily integration smoke against frozen scenario packs.
- Milestone demos scored by rubric dimensions.
- Release rehearsal on one pilot project before each stage change.

## Rollout/rollback
Rollout:
1. Merge contracts and scaffolds first.
2. Enable module flags gradually by workstream.
3. Activate operator pilot and monitor gates.
4. Expand cohort only after two clean cycles.

Rollback:
- Revert latest feature flags by module.
- Restore last-good dashboard artifacts.
- Freeze risky workstream merges until root cause resolved.

## Risks and mitigations
- Risk: schedule slip from cross-team blocking. Mitigation: critical path owner and escalation SLA.
- Risk: overload in QA and UX research. Mitigation: reserve dedicated capacity in WS6/WS8.
- Risk: too many concurrent changes on same files. Mitigation: strict ownership and branch discipline.
- Risk: under-scoped docs/training. Mitigation: WS8 starts at week 1, not after coding.

## Resource impact
- Staffing: 40 contributors across 8 squads.
- Delivery overhead: high coordination, controlled via weekly train.
- Tooling overhead: moderate; mostly CI replay and reporting.
- Expected gain: lower incident triage time and fewer release regressions.

## Ticket table
| ticket_id | owner_role | dependency_ids | dod | test_evidence | risk_level |
|---|---|---|---|---|---|
| TKT-UX-001 | frontend_lead | none | Define dashboard information architecture and card priority map approved by @leo. | IA review checklist + screenshot set. | medium |
| TKT-UX-002 | frontend_engineer | TKT-UX-001 | Implement one-screen summary shell with keyboard navigation. | Accessibility test report against S2/S4. | medium |
| TKT-UX-003 | frontend_engineer | TKT-UX-002 | Implement pressure-mode visual style and fallback text states. | Visual regression snapshots + offline run. | low |
| TKT-UX-004 | frontend_engineer | TKT-UX-002 | Build timeline panel with warning/critical markers. | Scenario replay screenshots (normal/degraded/incident). | medium |
| TKT-UX-005 | frontend_engineer | TKT-UX-002 | Build cost and usage panel with stale indicators. | Unit tests on metric formatting + stale badge logic. | low |
| TKT-DATA-001 | backend_lead | none | Freeze canonical snapshot schema v1. | JSON Schema validation suite (S3). | high |
| TKT-DATA-002 | backend_engineer | TKT-DATA-001 | Implement adapters for STATE/ROADMAP/DECISIONS inputs. | Contract tests on fixture projects. | medium |
| TKT-DATA-003 | backend_engineer | TKT-DATA-001 | Implement adapter for chat and agent journals. | Replay fixture diff = zero semantic drift. | medium |
| TKT-DATA-004 | backend_engineer | TKT-DATA-002,TKT-DATA-003 | Implement snapshot builder with deterministic sorting. | Determinism test 1000 runs pass. | high |
| TKT-DATA-005 | backend_engineer | TKT-DATA-004 | Implement atomic write path for snapshot and html outputs. | Fault-injection tests for partial write recovery. | high |
| TKT-ORCH-001 | reliability_lead | TKT-DATA-004 | Define update state machine and retry policy. | State transition tests and failure matrix. | high |
| TKT-ORCH-002 | reliability_engineer | TKT-ORCH-001 | Implement queue and fair scheduling with project quotas. | Load test with queue saturation scenarios. | high |
| TKT-ORCH-003 | reliability_engineer | TKT-ORCH-001 | Implement run bundle persistence and manifest hashes. | Replay hash consistency report. | high |
| TKT-ORCH-004 | reliability_engineer | TKT-ORCH-003 | Implement rollback-to-last-good logic. | Chaos test kill-renderer pass. | medium |
| TKT-MEM-001 | data_lead | TKT-DATA-001 | Implement project FTS index pipeline. | Query latency benchmark p95 target. | medium |
| TKT-MEM-002 | data_engineer | TKT-MEM-001 | Implement daily/weekly compaction with trace links. | Summary trace integrity tests. | medium |
| TKT-MEM-003 | data_engineer | TKT-MEM-002 | Implement promotion queue with @clems approval metadata. | Policy integration tests and audit log checks. | high |
| TKT-MEM-004 | ml_engineer | TKT-MEM-001 | Build optional semantic pilot behind feature flag. | A/B relevance report vs FTS baseline. | medium |
| TKT-POL-001 | security_lead | none | Finalize skill lockfile validation service. | Hash mismatch negative tests. | high |
| TKT-POL-002 | security_engineer | TKT-POL-001 | Implement approval API and expiry tokens. | API contract tests + denial path checks. | high |
| TKT-POL-003 | security_engineer | TKT-POL-002,TKT-ORCH-001 | Enforce policy gate in update workflow. | End-to-end policy violation tests. | high |
| TKT-POL-004 | security_engineer | TKT-POL-001 | Build skill trust panel backend feed. | Snapshot payload integrity checks. | medium |
| TKT-EVAL-001 | qa_lead | TKT-DATA-004,TKT-ORCH-003 | Build scenario pack format and fixture generator. | 20-pack validation pass. | medium |
| TKT-EVAL-002 | qa_engineer | TKT-EVAL-001 | Implement replay runner and verdict exporter. | CI replay report for all packs. | high |
| TKT-EVAL-003 | ux_research | TKT-UX-003,TKT-EVAL-001 | Build 60-second comprehension protocol and question bank. | Pilot study with confidence interval report. | medium |
| TKT-EVAL-004 | qa_engineer | TKT-EVAL-002,TKT-EVAL-003 | Enforce hard gates in release pipeline. | Simulated gate fail/pass run logs. | high |
| TKT-OBS-001 | sre_lead | TKT-ORCH-002 | Instrument update latency and queue metrics. | Dashboard with p50/p95/p99 panels. | medium |
| TKT-OBS-002 | sre_engineer | TKT-OBS-001 | Add stale-data and failure alerts. | Alert fire-drill logs. | medium |
| TKT-OBS-003 | finops | TKT-OBS-001 | Implement token and API cost telemetry rollups. | Budget report matched to raw usage. | low |
| TKT-DOC-001 | docs_lead | TKT-UX-001,TKT-POL-001 | Write operator runbook for pressure mode triage. | Dry-run checklist with 3 operators. | low |
| TKT-DOC-002 | docs_engineer | TKT-DOC-001 | Write rollback playbook with decision tree. | Tabletop incident simulation notes. | medium |
| TKT-DOC-003 | trainer | TKT-DOC-001,TKT-EVAL-003 | Build onboarding module for 60-second comprehension workflow. | Training completion and post-test scores. | low |
