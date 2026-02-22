# 02_ARCHITECTURE

## Context
This architecture is for Cockpit V2 Round 1 Variant A. The design optimizes for stability, persistence, and deterministic replay while preserving project memory isolation and full-access approval gates.

## Problem statement
A many-agent runtime fails in production when persistence is implicit, retries are ad hoc, and recovery is non-deterministic. We need an architecture that makes failure explicit and recoverable [P2][P6].

## Proposed design
### A. System components
- Orchestrator Core
- Persistent Event Store (append-only)
- Snapshot Manager
- Run Bundle Service
- Policy and Approval Service
- Memory Isolation Service
- Replay Engine
- Eval Harness Service

### B. Deterministic Run Bundle Contract (RBC)
Each run emits a sealed bundle:
- `bundle_id`
- `project_id`
- `run_id`
- `version`
- `input_digest`
- `events[]` (ordered, immutable)
- `tool_calls[]` with result digests
- `approval_events[]`
- `output_digest`
- `hash_chain_root`
- `created_at`, `sealed_at`

Rules:
- RBC seal is monotonic and immutable after commit.
- Replay must reproduce `output_digest` and `hash_chain_root`.
- If mismatch: mark run `non_deterministic`, block promotion, raise incident.

### C. State machine for retries/timeouts/backoff
States:
- `NEW`
- `RUNNING`
- `WAITING_DEPENDENCY`
- `RETRY_SCHEDULED`
- `COMMIT_PREPARED`
- `COMMITTED`
- `FAILED_TRANSIENT`
- `FAILED_PERMANENT`
- `ROLLED_BACK`

Transitions:
- `NEW -> RUNNING` on orchestrator admission.
- `RUNNING -> WAITING_DEPENDENCY` on external dependency wait.
- `WAITING_DEPENDENCY -> RETRY_SCHEDULED` on timeout.
- `RETRY_SCHEDULED -> RUNNING` after backoff window.
- `RUNNING -> COMMIT_PREPARED` after successful deterministic checks.
- `COMMIT_PREPARED -> COMMITTED` on atomic commit.
- `RUNNING -> FAILED_TRANSIENT` on retryable failure.
- `RUNNING -> FAILED_PERMANENT` on policy or corruption violation.
- `FAILED_TRANSIENT -> ROLLED_BACK` when retry budget exceeded.

Backoff contract:
- exponential with jitter
- max attempts per class
- max wall-clock budget per run
- reset policy after successful dependency response

### D. Atomic persistence design
- WAL first, then materialized views.
- Commit uses `prepare/commit` with idempotency key.
- Reader view always built from consistent checkpoint + WAL tail.
- Corruption guard: per-record checksum and sequence continuity checks [R6].

### E. Isolation boundaries
- Project-scoped stores for chat, run bundles, journals, memory indexes.
- Global Brain is read-only for generic assets from project runtime.
- Promotion path only through approval workflow with explicit policy event.

## Interfaces and contracts
### Interface: Run lifecycle
- `POST /runs`
- `POST /runs/{id}/events`
- `POST /runs/{id}/seal`
- `POST /runs/{id}/replay`
- `POST /runs/{id}/rollback`

### Interface: Approval
- `POST /approvals/full-access/request`
- `POST /approvals/{id}/grant`
- `POST /approvals/{id}/deny`

### Interface: Memory
- `PUT /memory/projects/{project_id}/items`
- `GET /memory/projects/{project_id}/items/{item_id}`
- `POST /memory/promotions` (requires approval token)

Contract invariants:
- Exactly-once logical effect for idempotent operations.
- Event ordering invariant by `(project_id, run_id, seq)`.
- Policy invariant: any full-access action must reference approval id.

## Failure modes
- FM1: Disk full during WAL append.
  - Handling: fail write, no commit, run becomes `FAILED_TRANSIENT`, alert raised.
- FM2: Replay hash mismatch.
  - Handling: block release lane, quarantine bundle, trigger forensic task.
- FM3: Approval service unavailable.
  - Handling: fail closed for full-access tasks, continue workspace-only tasks.
- FM4: Snapshot lag too high.
  - Handling: throttle new admissions and prioritize compaction workers.
- FM5: Duplicate run_id due to client retry.
  - Handling: idempotent create returns prior run metadata.

## Validation strategy
- Determinism suite from recorded run bundles [P7].
- Fuzz tests for event ordering and duplicate delivery.
- Crash-at-every-line harness for commit path.
- Policy conformance tests for approval-required actions.
- Recovery drill: restore from snapshot + WAL under injected corruption.

## Rollout/rollback
- Phase 0: design review and contract freeze.
- Phase 1: shadow recording of bundles.
- Phase 2: dual write and replay comparison.
- Phase 3: pilot projects with strict SLOs.
- Phase 4: broad rollout with guardrail dashboards.

Rollback guardrails:
- rollback on deterministic mismatch ratio > threshold
- rollback on data corruption signal
- rollback on policy gate bypass signal

## Risks and mitigations
- Risk: bundle growth and storage cost.
  - Mitigation: compaction, TTL for non-critical bundles, archival tiers.
- Risk: complexity in state machine implementation.
  - Mitigation: explicit transition table and model-based tests.
- Risk: release slowdown due to strict gates.
  - Mitigation: parallelized validation and clear bypass policy only for non-critical lanes.

## Resource impact
- Platform engineering: high for first two milestones.
- SRE workload: medium-high for replay and corruption observability.
- Storage budget: moderate increase due to append-only policy.
- Developer productivity: short-term hit, long-term gain from lower incident volume.

Evidence tags used: [P2][P4][P6][P7][P8][R1][R2][R3][R6][S1][S2].
