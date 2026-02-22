# Wave04 Operator Packet Draft - 2026-02-19

## Goal
- Provide one-page execution control for Wave04.

## Current status
- Phase: Implement
- Gates at T0:
  - pending_stale_gt24h=0
  - queued_runtime_requests=0
  - stale_heartbeats_gt1h=0
- Active chains:
  - C0 control loop
  - C1 UI ship lock
  - C2 backend contract lock
  - C3 cleanup decisions
  - C4 dispatch/packet lock

## Required checkpoints
1. T+120 Gate 1
- C0 green
- C1 matrix + captures complete
- C2 tests + determinism complete
2. T+240 Gate 2
- all Gate 1 checks still green
- operator packet finalized
3. T+360 closeout
- next-wave dispatch lock

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/PAPER_PLAN_WAVE04_PARALLELIZATION_MAX_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE04_DISPATCH_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE04_GATE_CHECKLIST_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/control_snapshot_wave04_t0_2026-02-19.md
