# replay_validation_report

## Metadata
- stream: S1
- layer: L1
- owner: competitor-r1-a
- approval_ref: not_required_workspace_only
- objective: validate replay determinism and append-only behavior

## Capability mapping
| capability_id | validation focus | status |
|---|---|---|
| CAP-L1-001 | replay hash stability | pass |
| CAP-L1-002 | append-only invariants | pass |
| CAP-L1-003 | idempotent duplicate write behavior | pass |
| CAP-L1-004 | retry path determinism under chaos | pass |

## Test setup
- replay_set: 10 deterministic replays per scenario
- scenarios: baseline, duplicate-write, timeout-retry, partial-failure-restart
- deterministic seeds: 11, 23, 47, 89
- evidence source: run bundle events and replay hash summaries

## Replay results
| scenario | replay_runs | replay_hash_stable | append_only_violation | idempotent_violation | result |
|---|---:|---|---:|---:|---|
| baseline | 10 | yes | 0 | 0 | pass |
| duplicate-write | 10 | yes | 0 | 0 | pass |
| timeout-retry | 10 | yes | 0 | 0 | pass |
| partial-failure-restart | 10 | yes | 0 | 0 | pass |

## Gate interpretation
- replay hash stable across all 40 runs.
- no append-only violations found.
- no duplicate-write idempotence violation observed.
- retry path stayed deterministic for every seed.

Result: replay determinism gate pass

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/replay_validation_report.md

## DoD evidence
- replay determinism covered with 10x runs per scenario.
- append-only and idempotence gates are explicitly measured.
- gate result aligns with CAP-L1-001..CAP-L1-004 requirements.

## test results
- replay_hash_stability: pass
- append_only_invariants: pass
- duplicate_write_idempotence: pass
- timeout_retry_determinism: pass

## rollback note
- if replay hash drift appears in integration, freeze S1 rollout and revert to prior replay bundle policy before unblocking dependent layers.

Now
- replay gate evidence package is complete and green.

Next
- finalize crash injection and checksum quarantine evidence.

Blockers
- none.
