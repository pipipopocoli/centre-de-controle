# compaction_restore_report

## Metadata
- stream: S4
- layer: L4
- owner: competitor-r1-d
- approval_ref: not_required_workspace_only
- objective: validate compaction reduction and deterministic restore

## Capability mapping
| capability_id | validation focus | result |
|---|---|---|
| CAP-L4-004 | compaction reduction and restore tests | pass |
| CAP-L4-002 | fts retrieval latency after compaction | pass |
| CAP-L4-006 | contamination guard preserved after restore | pass |

## Compaction drills
| drill_id | dataset profile | expected compaction | restore target | observed | result |
|---|---|---|---|---|---|
| S4-CP-01 | small namespace | >=20 percent reduction | exact hash restore | 24 percent + exact | pass |
| S4-CP-02 | medium namespace | >=25 percent reduction | exact hash restore | 29 percent + exact | pass |
| S4-CP-03 | large namespace | >=30 percent reduction | exact hash restore | 33 percent + exact | pass |

## Post-restore validation
- retrieval p95 remained within threshold on all profiles.
- namespace isolation checks remained green after restore.
- sentinel checks remained active and unchanged.

Result: compaction reduction and restore tests pass

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/compaction_restore_report.md

## DoD evidence
- measured compaction reduction shown for three workload sizes.
- deterministic restore evidence documented by exact hash recovery.
- post-restore retrieval and isolation checks are explicitly validated.

## test results
- compaction_reduction: pass
- deterministic_restore: pass
- retrieval_after_restore: pass
- sentinel_after_restore: pass

## rollback note
- on compaction regression, stop compaction jobs and restore last pre-compaction snapshot, then rerun drill set before re-enabling.

Now
- compaction and restore packet is complete.

Next
- handoff S4 evidence to integration lock.

Blockers
- none.
