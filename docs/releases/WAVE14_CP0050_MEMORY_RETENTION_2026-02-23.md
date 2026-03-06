# Wave14 CP-0050 - Memory Retention Closeout (2026-02-23)

## Objective
Close CP-0050 with enforceable 7d/30d/90d/permanent retention in memory indexing, without source purge and without isolation regression.

## Retention policy enforced (7/30/90/permanent)
- Mode: index+manifest only (no destructive delete).
- Tier contract:
  - hot_7d: indexed full recent signals
  - warm_30d: indexed short normalized signals
  - cool_90d: indexed compact signals
  - archive_permanent: not indexed as raw rows, archived via deterministic gzip when present
- Operator wording pass (@agent-11):
  - 7d hot / 30d warm / 90d cool / >90d permanent archive
  - Operator action in <=60s: run memory index build, check retention_status, then post Now/Next/Blockers.

## Isolation proof
- Canonical root enforcement remains in store helpers with project canonicalization.
- retention_status isolation_check:
  - canonical_project_id: cockpit
  - projects_root: /Users/oliviercloutier/Desktop/Cockpit/control/projects
- Regression checks passed:
  - ./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_index.py
  - ./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave12_isolation.py

## Current status + next compaction
- status path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
- policy_version: wave14-7-30-90-permanent-v1
- generated_at: 2026-02-23T10:27:53+00:00
- next_compaction_at: 2026-02-23T12:27:53+00:00
- totals:
  - hot_7d: 80
  - warm_30d: 109
  - cool_90d: 0
  - archive_permanent: 0

## Deep RnD D1
- D1 | recommendation: retention confidence score from timestamp quality + tier coverage.
- owner: @victor
- next_action: add deterministic tests for timestamp_missing/invalid/old rows and track confidence in retention_status.json.
- evidence_path:
  - /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
- decision_tag: adopt

## Now/Next/Blockers
- Now: CP-0050 retention enforcement is active in memory indexing and status artifact writes on build.
- Next: monitor next_compaction_at and confirm archive behavior when >90d rows appear.
- Blockers: none.

## Evidence paths
- /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/app/data/store.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
