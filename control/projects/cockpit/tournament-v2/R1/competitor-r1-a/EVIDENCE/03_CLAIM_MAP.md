# Claim Map

| claim_id | claim summary | backing type | references |
|---|---|---|---|
| C-001 | Deterministic replay reduces recovery ambiguity | source-backed | P2, P7 |
| C-002 | Append-only log + snapshots improves crash recovery | source-backed | P4, P7, R3 |
| C-003 | Explicit state machine for retries lowers hidden failure modes | source-backed | P2, P8 |
| C-004 | Policy fail-closed for full-access actions prevents unsafe execution | source-backed | P6, S1 |
| C-005 | Idempotency keys are required for safe retries | source-backed | P8, R1 |
| C-006 | Project memory isolation must be default | source-backed | P3, P5 |
| C-007 | Promotion to Global Brain should require governance gate | source-backed | P6, S2 |
| C-008 | Corruption checksums and sequence checks reduce silent data loss | source-backed | P4, R6 |
| C-009 | 16-week roadmap is feasible for 40-dev team | ASSUMPTION | ASSUMPTION-A5 |
| C-010 | Baseline subscription can absorb R1/R2 load profile | ASSUMPTION | ASSUMPTION-A1 |
| C-011 | Operator can act in 60 seconds with structured cards | ASSUMPTION | ASSUMPTION-A6 |
| C-012 | Semantic retrieval can remain optional during initial rollout | ASSUMPTION | ASSUMPTION-A7 |
| C-013 | Replay and crash suites can serve as release-blocking gates | source-backed | P7, R2, R4 |
| C-014 | Skill pinning by commit hash improves replay consistency | source-backed | R1, R6 |
| C-015 | Rollback drills reduce incident MTTR | source-backed | P7, R2 |
