# Roadmap

## Vision
- Ship cockpit implementation continuously, with tournament-v2 feeding improvements in parallel.

## Priorities
- P0: close V2-WAVE-03 core issues (CP-0004, CP-0005, CP-0015)
- P1: queue/heartbeat control gates stay green during execution
- P2: keep tournament streams as dormant optional capability
- P3: prepare next implementation wave from validated deltas only

## Sequence
1. CP-0004 complete: deterministic memory index output delivered and validated.
2. CP-0005 complete: MCP skills tools delivered and payload compatibility locked.
3. CP-0015 complete: QA evidence pack published for checkpoint closeout.
4. Runtime queue/heartbeat gates swept and closeout snapshot locked (2026-02-19).
5. Backend/control closeout validation complete: MCP routing/tools checks locked and payload non-regression confirmed.
6. Move from Review to Ship after final operator signoff packet.

## Daily control gates
- pending stale (24h+): must be 0
- stale heartbeats (1h+): must be <= 2
- queued runtime requests: must be <= 3
- wave03 issue close rate: must be 3/3 by sprint closeout

## Active source of truth
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/control_snapshot_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/queue_recovery_2026-02-19.ndjson
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2_RELAUNCH_DISPATCH_2026-02-18.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_QA_EVIDENCE_PACK_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_EVIDENCE_DELTA_P0.md
