# Round 0 - V1 Baseline From Leo Source

## Goal
- Convert Leo source spec into one V1 baseline that can drive implementation decisions without additional interpretation.
- Keep all strategic intent while simplifying into V1 execution layers.

## Source Lock
- Canonical input: `/Users/oliviercloutier/Desktop/Cockpit/docs/cockpit_v2_project_spec.md`
- Extraction date: `2026-02-13`
- Project lock: `cockpit`

## Chapter Coverage Matrix
| Leo Source Chapter | Coverage In V1 Baseline | Notes |
|---|---|---|
| 1. Contexte and justification | Full | Converted into V1 problem statement and success KPIs |
| 2. Architecture cible V2 | Full | Normalized into V1 architecture map and constraints |
| 3. Plugin 1 registry and hierarchy | Full | Kept as mandatory V1 foundation |
| 4. Plugin 2 soul and skills | Full | Reduced to V1 minimal viable dynamic skills |
| 5. Plugin 3 task manager | Full | Reframed as workflow cockpit view |
| 6. Plugin 4 platform router | Full | Kept with fallback and retry policy |
| 7. Plugin 5 memory progressive | Full | Split into V1 FTS baseline + deferred vector step |
| 8. hardware and infra | Full | Converted into operating constraints and runbook |
| 9. dependencies | Full | Converted into phased dependency policy |
| 10. roadmap and tasks | Full | Rebased into V1-first roadmap sequence |
| 11. risks and mitigations | Full | Converted into risk register with owner and test gate |

## V1 Baseline Statement
- V1 is not a prototype.
- V1 is the first production-grade operating model for Cockpit where:
1. Agent hierarchy is explicit and observable.
2. Workflow state is operator-readable in less than 60 seconds.
3. Runtime dispatch is resilient to primary runtime failure.
4. Memory is persistent enough to avoid repeated mistakes.
5. Program Bible is the daily source of truth for why/how work is executed.

## V1 Baseline Workstreams

### P0 - Program Bible Architecture And AI Workflow
- Define bible structure, ownership model, and update protocol.
- Define operator to lead to specialist flow with decision gates.
- Define required evidence per delivery item.

DoD
- Program Bible chapter map approved.
- Update cadence and ownership rules documented.
- Gate checklist integrated with roadmap and state docs.

Risks
- Too theoretical, low execution value.
- Duplicate truth sources.

Tests
- Review drill: can a new operator understand project state in 10 minutes?
- Trace drill: can a decision be traced to one chapter and one owner?

### P1 - UX And Operator Flow Clarity
- Move from status noise to action states: repos, en action, attente reponse, bloque.
- Show mission context and blockers in one glance.
- Tighten handoff messages and response lifecycle.

DoD
- UI state model documented and consistent with process docs.
- Handoff template standardized.
- Escalation and reminder logic documented.

Risks
- Overloaded dashboards.
- Inconsistent wording across files.

Tests
- Operator latency test: identify top blocker in under 30 seconds.
- Ambiguity test: no status can be interpreted in two opposite ways.

### P2 - Architecture Risk And Runtime Contracts
- Define contracts for registry, router, state, and skills loader.
- Define fallback rules and failure states.
- Define rollout and rollback envelopes.

DoD
- Contracts include input, output, invariants, and failure behavior.
- Risk register has owner, mitigation, and test gate.
- Rollback steps executable without hidden decisions.

Risks
- Contract drift between docs and implementation.
- Hidden runtime assumptions.

Tests
- Contract simulation with invalid payloads.
- Failure injection scenarios for runtime fallback.

### P3 - Execution Breakdown, Test Gates, Rollout
- Convert baseline into sequence of reversible implementation lots.
- Define hard quality gates before merge.
- Define release and post-release checks.

DoD
- Sequence table with lot order, owner, dependencies, acceptance test.
- Rollout plan and rollback plan published.
- Post-release monitoring checklist published.

Risks
- Scope creep before V1 lock.
- Gate skipping under time pressure.

Tests
- Dry-run of full gate path on paper.
- Review packet completeness test.

## V1 Baseline Decisions (Locked)
1. Program Bible becomes mandatory project truth artifact.
2. `ROADMAP.md` and `STATE.md` are rebased to V1-first immediately.
3. Round model is mandatory before code implementation.
4. Weighted scorecard is the single arbitration mechanism.
5. Two outlier tracks are mandatory (`@agent-14`, `@agent-15`).
6. No API change during tournament phase.
7. Every proposal item requires problem/proposal/impact/risk/test/DoD.
8. Compile docs must include accept/reject/defer trace.
9. Critical unresolved risk can veto a high score.
10. Final operator packet is required before implementation kickoff.

## Program Bible V1 Table Of Contents
1. Mission and strategic objective
2. Workflow operating system
3. Roles, hierarchy, and delegation contracts
4. Runtime and dispatch contracts
5. State model and observability model
6. Memory and learning model
7. Risk register and mitigations
8. Execution sequence and gates
9. Rollout, rollback, and recovery
10. Decision log and change control

## Baseline Acceptance Gates

### Gate 0 Checklist
- No direct contradiction between baseline chapters.
- All chapters have objective + DoD + risks + tests.
- All owner responsibilities are explicit.
- All phase exits are measurable.
- No chapter depends on undefined future decisions.

## Assumptions
- Leo source spec intent is valid and remains top priority.
- Current CP-01 docs are preserved as historical context, not V1 truth source.
- Tournament docs are authoritative for planning until implementation starts.
