# Roadmap

## Vision
- Ship cockpit implementation continuously, with tournament-v2 feeding improvements in parallel.

## Priorities
- P0: execute Wave04 chains C0-C4 without breaking runtime control.
- P1: keep queue/heartbeat gates green throughout execution.
- P2: keep tournament streams as dormant optional capability.
- P3: prepare next implementation wave from validated deltas only.

## Sequence
1. Wave03 closeout lock confirmed (CP-0004/0005/0015).
2. Wave04 kickoff artifacts published (paper plan + dispatch + gate checklist).
3. C1 UI ship lock lane and C2 backend contract lane execute in parallel.
4. C0 control cadence validates gates at T+0, T+120, T+240.
5. C3 cleanup canonicalization publishes decisions (no destructive cleanup).
6. C4 finalizes Wave04 dispatch/order and operator packet.
7. Gate 2 decision publishes ship-ready packet if all chains are green.

## Daily control gates
- pending stale (24h+): must be 0
- stale heartbeats (1h+): must be <= 2
- queued runtime requests: must be <= 3
- wave04 chain coverage: C0/C1/C2/C3/C4 all tracked

## Active source of truth
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/PAPER_PLAN_WAVE04_PARALLELIZATION_MAX_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE04_DISPATCH_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE04_GATE_CHECKLIST_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/control_snapshot_wave04_t0_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/queue_recovery_2026-02-19.ndjson
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_QA_EVIDENCE_PACK_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_EVIDENCE_DELTA_P0.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_CLEANUP_V2.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md
