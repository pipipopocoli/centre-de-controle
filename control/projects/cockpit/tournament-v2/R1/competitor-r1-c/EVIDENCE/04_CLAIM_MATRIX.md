# Claim to Source Matrix

Context
- Maps major design claims to evidence or assumptions.

Problem statement
- Large plans become non-verifiable when claims are not tied to sources.

Proposed design
- Explicit claim IDs with source references.

Interfaces and contracts
- Claim record fields:
  - claim_id
  - claim
  - backing_type (source or ASSUMPTION)
  - evidence_ids
  - validation_plan

Failure modes
- Missing evidence IDs.
- Claims mapped to weakly relevant sources.

Validation strategy
- No claim without backing_type.
- All evidence IDs exist in evidence files.

Rollout/rollback
- Rollout: use this matrix as gate before scoring.
- Rollback: if source invalid, flip to ASSUMPTION with deadline.

Risks and mitigations
- Risk: stale evidence.
- Mitigation: refresh matrix every round.

Resource impact
- Medium documentation overhead.

## Claims
- CLM-001 | Router must support deterministic replay bundles for incident analysis | source | SRC-P1,SRC-P5,SRC-R1 | replay drill with fixed event seed.
- CLM-002 | Queue model should be append-log first, not transient memory only | source | SRC-P9,SRC-R2,SRC-R3 | failover simulation preserves unacked work.
- CLM-003 | Fallback tiers should optimize tail latency, not mean latency only | source | SRC-P6,SRC-R5 | p95 and p99 benchmark gates.
- CLM-004 | Scheduler fairness needs explicit anti-thundering-herd controls | source | SRC-P10,SRC-R4,SRC-R6 | burst test with fairness SLO.
- CLM-005 | Leader election and lock coordination need explicit contracts | source | SRC-P3,SRC-P8 | split-brain chaos test.
- CLM-006 | Skills execution must remain workspace-only by default | source | SRC-D3 | permission matrix policy test.
- CLM-007 | Cross-project memory retrieval must stay disabled by default | source | SRC-D1 | contamination test with sentinel docs.
- CLM-008 | Promotion into Global Brain requires @clems approval and evidence packet | ASSUMPTION | ASSUMPTION-A1 | operator signoff dry run.
- CLM-009 | A two-queue scheduler (interactive and batch) reduces starvation | source | SRC-P4,SRC-P10,SRC-R5 | mixed workload soak test.
- CLM-010 | Circuit breaker state must be persisted for deterministic recovery | source | SRC-P2,SRC-R8 | restart test keeps breaker state.
- CLM-011 | Replay packs should include trace context IDs across providers | source | SRC-D1,SRC-D2,SRC-P5 | replay integrity check.
- CLM-012 | Worker fanout needs token-budget guardrail per mission | ASSUMPTION | ASSUMPTION-A2 | cost simulation with monthly cap.
