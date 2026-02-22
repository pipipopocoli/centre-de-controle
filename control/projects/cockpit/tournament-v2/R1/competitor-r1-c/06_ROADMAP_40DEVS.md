# 06_ROADMAP_40DEVS - Work Breakdown and Ticketized Execution

## Context
- This roadmap converts the Variant C architecture into an execution plan sized for a 40-dev team.
- Objective is decision-complete sequencing with explicit dependencies and test evidence.

## Problem statement
- High-level architecture without ticketized execution fails under parallel development.
- We need a workstream-based WBS and hard DoD evidence per ticket.

## Proposed design
### Workstream breakdown structure
- WS-01 Router core and policy ingress
- WS-02 Scheduler fairness and queue system
- WS-03 Provider adapters and fallback coordinator
- WS-04 Replay, event store, and traceability
- WS-05 Memory isolation and promotion controls
- WS-06 Eval harness and release gates
- WS-07 Operator vulgarisation and reporting

### Milestones
- M1 (Week 1-4): Router skeleton + queue baseline + replay contract.
- M2 (Week 5-8): Fairness logic + fallback tiers + memory policy hardening.
- M3 (Week 9-12): Eval harness full gates + cost guardrails + dashboards.
- M4 (Week 13-16): Reliability hardening, load tests, rollout prep.

### Critical path
- PolicyEngine -> SchedulerCore -> QueueManager -> FallbackCoordinator -> ReplayWriter -> EvalGates.

## Interfaces and contracts
- Ticket contract fields:
  - ticket_id
  - owner_role
  - dependency_ids
  - dod
  - test_evidence
  - risk_level
- Dependency rules:
  - no implementation ticket starts without contract ticket complete.
  - no rollout ticket starts without eval gate ticket complete.

## Failure modes
- FM-RM-01: dependency inversion causes integration deadlock.
- FM-RM-02: too many parallel high-risk tickets increase churn.
- FM-RM-03: weak DoD definitions allow hidden regressions.

## Validation strategy
- Weekly dependency audit.
- WIP cap per workstream.
- Mandatory test evidence checks in ticket closure.

## Rollout/rollback
- Rollout: by milestone gates M1-M4.
- Rollback: freeze active workstream and revert to prior milestone baseline.

## Risks and mitigations
- Risk: staffing imbalance among workstreams.
  - Mitigation: weekly rebalance by blocker pressure.
- Risk: ticket granularity too coarse.
  - Mitigation: enforce max ticket scope and split rule.

## Resource impact
- 40-dev allocation:
  - WS-01: 6
  - WS-02: 8
  - WS-03: 7
  - WS-04: 6
  - WS-05: 4
  - WS-06: 6
  - WS-07: 3

## Ticket table (mandatory)
| ticket_id | title | owner_role | dependency_ids | estimate | risk_level | dod | test_evidence | rollback |
|---|---|---|---|---|---|---|---|---|
| TKT-C-001 | Router request schema v1 | victor | none | 3d | medium | schema approved and documented | schema validation tests | revert schema to v0 |
| TKT-C-002 | PolicyGate decision engine | victor | TKT-C-001 | 5d | high | deny rules and allow rules implemented | policy unit tests + fuzz deny tests | disable policy plugin and safe deny |
| TKT-C-003 | ApprovalGate integration | clems | TKT-C-002 | 3d | high | elevated actions blocked without approval_ref | integration tests on elevated actions | force all elevated actions blocked |
| TKT-C-004 | Scheduler core baseline | victor | TKT-C-001 | 6d | high | scheduler selects queue and provider deterministically | deterministic seed tests | switch to static queue order |
| TKT-C-005 | QueueManager interactive lane | victor | TKT-C-004 | 4d | medium | interactive queue with bounded depth | queue load tests | fallback to in-memory queue |
| TKT-C-006 | QueueManager batch lane | victor | TKT-C-004 | 4d | medium | batch queue with persistence | batch drain tests | disable batch lane |
| TKT-C-007 | Fairness credit controller | victor | TKT-C-005,TKT-C-006 | 6d | high | starvation guard active | 24h mixed-load test | disable credits and run RR safe mode |
| TKT-C-008 | Anti-thundering-herd token bucket | victor | TKT-C-007 | 4d | high | burst admission limits enforced | burst chaos benchmark | fixed cap mode |
| TKT-C-009 | Retry/backoff state machine | victor | TKT-C-004 | 5d | high | bounded retries and jitter policy | failure injection tests | disable retries above threshold |
| TKT-C-010 | FallbackCoordinator Tier0-3 | victor | TKT-C-009 | 6d | high | fallback tiers dispatch correctly | outage simulation suite | force Tier3 hold |
| TKT-C-011 | CodexAdapter normalized payload | worker | TKT-C-001 | 5d | medium | adapter contract passes schema | adapter contract tests | disable adapter |
| TKT-C-012 | AntigravityAdapter normalized payload | worker | TKT-C-001 | 5d | medium | adapter contract passes schema | adapter contract tests | disable adapter |
| TKT-C-013 | Optional adapter feature flag | worker | TKT-C-011,TKT-C-012 | 3d | medium | optional adapter disabled by default | flag behavior tests | hard disable optional adapter |
| TKT-C-014 | Provider health monitor | worker | TKT-C-011,TKT-C-012 | 4d | medium | health probes feed scheduler | failover readiness tests | static provider health table |
| TKT-C-015 | ReplayBundleWriter v1 | victor | TKT-C-004 | 5d | high | event bundles persisted with checksum | replay integrity tests | disable writes and hold runs |
| TKT-C-016 | EventStore retention policy | worker | TKT-C-015 | 4d | medium | retention jobs and index compaction | retention simulation | revert to full retention |
| TKT-C-017 | TraceCollector integration | worker | TKT-C-015 | 4d | medium | trace ids linked to run ids | trace continuity tests | disable trace export |
| TKT-C-018 | EvalHarnessBridge API | victor | TKT-C-015,TKT-C-017 | 4d | medium | harness consumes replay bundles | bridge integration tests | disable bridge and manual ingestion |
| TKT-C-019 | Memory query scope guard | victor | TKT-C-002 | 4d | high | cross-project retrieval blocked by default | contamination tests | emergency deny-all retrieval |
| TKT-C-020 | Promotion workflow with approval | clems | TKT-C-003,TKT-C-019 | 4d | high | promotion requires approval packet | promotion audit tests | pause promotions |
| TKT-C-021 | Memory compaction baseline | worker | TKT-C-019 | 5d | medium | stale records summarized with provenance | compaction quality tests | disable compaction |
| TKT-C-022 | Skills lockfile validator | victor | TKT-C-002 | 3d | medium | pinned hash checks enforced | lockfile integrity tests | deny non-pinned skills |
| TKT-C-023 | Skill assignment policy checks | victor | TKT-C-022 | 4d | medium | assignment requires scope+expiry+fallback | assignment lint tests | disable dynamic assignment |
| TKT-C-024 | Souls heartbeat monitor | worker | TKT-C-002 | 3d | low | stale heartbeats produce alerts | heartbeat simulation tests | static status mode |
| TKT-C-025 | Eval suite A replay determinism | victor | TKT-C-018 | 5d | high | replay pass rate threshold enforced | replay suite reports | release block on failure |
| TKT-C-026 | Eval suite B fairness soak | victor | TKT-C-007,TKT-C-018 | 5d | high | starvation threshold enforced | 24h soak reports | fallback to safe scheduler |
| TKT-C-027 | Eval suite C outage fallback | victor | TKT-C-010,TKT-C-018 | 4d | high | fallback path correctness enforced | outage chaos reports | force Tier3 |
| TKT-C-028 | Eval suite D policy fuzzing | victor | TKT-C-002,TKT-C-018 | 4d | high | bypass attempts blocked | fuzz test reports | lock routing ingress |
| TKT-C-029 | Eval suite E budget guards | victor | TKT-C-008,TKT-C-018 | 4d | medium | budget stop and escalation works | budget simulation logs | disable high-cost runs |
| TKT-C-030 | Gate runner in CI | worker | TKT-C-025,TKT-C-026,TKT-C-027,TKT-C-028,TKT-C-029 | 4d | medium | gate runner blocks failed releases | CI gate logs | bypass only with @clems approval |
| TKT-C-031 | Vulgarisation config schema | leo | TKT-C-001 | 3d | low | config schema documented | schema validation tests | revert to static panel |
| TKT-C-032 | Offline dashboard generator | leo | TKT-C-031 | 5d | medium | local html generated atomically | offline open tests | keep last good html |
| TKT-C-033 | Metrics and timeline panels | leo | TKT-C-032,TKT-C-017 | 4d | medium | timeline and metrics render with placeholders | render regression tests | hide panel on error |
| TKT-C-034 | Skill inventory panel | leo | TKT-C-022,TKT-C-032 | 3d | low | skill trust info visible | panel unit tests | hide inventory panel |
| TKT-C-035 | Cost panel integration | leo | TKT-C-029,TKT-C-032 | 3d | medium | cost telemetry shown with freshness | panel integration tests | fallback to no-cost placeholder |
| TKT-C-036 | Incident runbook draft | clems | TKT-C-010,TKT-C-030 | 3d | medium | runbook covers kill-switch and command chain | tabletop drill evidence | revert to prior runbook |
| TKT-C-037 | Kill-switch automation | victor | TKT-C-036,TKT-C-030 | 4d | high | kill-switch enforces hold state | kill-switch drills | manual hold fallback |
| TKT-C-038 | Capacity model and SLO dashboard | victor | TKT-C-007,TKT-C-029 | 4d | medium | p95/p99 and queue depth SLO board | SLO dashboard snapshots | static threshold alerts |
| TKT-C-039 | Rollout playbook M1-M4 | clems | TKT-C-030,TKT-C-036 | 3d | medium | phase gates and approvals documented | rollout checklist simulation | pause rollout |
| TKT-C-040 | Final readiness review packet | clems | TKT-C-039,TKT-C-038 | 2d | medium | readiness packet complete and signed | signoff artifact | delay release |
