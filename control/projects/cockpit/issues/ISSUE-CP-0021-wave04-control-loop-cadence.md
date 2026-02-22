# ISSUE-CP-0021 - Wave04 control loop cadence

- Owner: clems
- Phase: Implement
- Status: Done

## Objective
- Keep runtime gates green on a fixed 60-minute cadence during Wave04.

## Scope (In)
- control snapshots
- queue recovery trace updates
- gate review in STATE/ROADMAP

## Scope (Out)
- feature implementation
- tournament dispatch

## Done (Definition)
- 3 gate checks completed (T+0, T+120, T+240).
- Each check has evidence snapshot.
- No gate drift unresolved at closeout.

## Test/QA
- Verify:
  - `pending_stale_gt24h == 0`
  - `queued_runtime_requests <= 3`
  - `stale_heartbeats_gt1h <= 2`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE04_GATE_CHECKLIST_2026-02-19.md
