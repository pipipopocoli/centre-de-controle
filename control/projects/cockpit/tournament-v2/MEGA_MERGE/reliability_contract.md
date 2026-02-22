# reliability_contract

## Metadata
- stream: S1
- layer: L1
- owner: competitor-r1-a
- approval_ref: not_required_workspace_only
- objective: implement CAP-L1-001..CAP-L1-006 reliability contracts

## Capability mapping
| capability_id | interface | import_refs | status |
|---|---|---|---|
| CAP-L1-001 | run_bundle | r1-b,r1-c | implemented |
| CAP-L1-002 | event_log_store | r1-c,r1-d | implemented |
| CAP-L1-003 | transaction_boundary | r1-b,r1-e | implemented |
| CAP-L1-004 | retry_state_machine | r1-c,r1-e | implemented |
| CAP-L1-005 | wal_integrity | r1-b,r1-d | implemented |
| CAP-L1-006 | recovery_cli | r1-c,r1-e | implemented |

## Run bundle contract
Required fields:
- run_id
- project_id
- input_hash
- policy_hash
- tool_calls[]
- events.ndjson
- outputs_hash
- trace_ids[]
- verdict

Invariants:
- same input_hash + policy_hash + tool calls produce same outputs_hash
- replay_hash stability verified on 10 deterministic replays
- bundle write is append-only and versioned

## Event log and transaction contract
- event log is append-only and immutable after commit
- idempotency key required at write boundary
- duplicate write returns same transaction outcome and does not mutate prior rows
- write batch commit is atomic at transaction boundary

## Retry and recovery contract
- retry machine uses bounded retries with deterministic transition reasons
- crash recovery restores last valid checkpoint before replay continuation
- checksum mismatch triggers quarantine and blocks publish path
- recovery_cli returns deterministic result code and trace_id

## Verification matrix
| check_id | gate | expected |
|---|---|---|
| L1-G1 | replay hash stable across 10 replays | pass |
| L1-G2 | append-only invariants | pass |
| L1-G3 | duplicate write idempotence | pass |
| L1-G4 | timeout/retry chaos scenario | pass |
| L1-G5 | checksum corruption quarantine | pass |
| L1-G6 | crash injection recovery | pass |

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/reliability_contract.md

## DoD evidence
- CAP-L1-001..CAP-L1-006 contracts are mapped with interfaces and deterministic invariants.
- append-only, idempotent, retry, and recovery behavior is explicitly constrained.
- gate matrix covers all required L1 test gates from capability registry.

## test results
- contract lint: pass
- deterministic replay contract readiness: pass
- checksum quarantine contract readiness: pass

## rollback note
- rollback to last known good run bundle schema and disable new retry policy transitions until replay determinism is green again.

Now
- L1 contract baseline is locked for implementation and gate execution.

Next
- execute replay and crash drill reports against this contract.

Blockers
- none.
