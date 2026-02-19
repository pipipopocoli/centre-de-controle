# Roadmap

## Vision
- Ship cockpit implementation continuously, with tournament-v2 feeding improvements in parallel.

## Priorities
- P0: close V2-WAVE-03 core issues (CP-0004, CP-0005, CP-0015)
- P1: queue/heartbeat control gates stay green during execution
- P2: keep tournament streams as dormant optional capability
- P3: prepare next implementation wave from validated deltas only

## Sequence
1. Complete CP-0004 deterministic memory index output and lock tests.
2. Complete CP-0005 MCP skills tools and lock payload compatibility.
3. Complete CP-0015 QA evidence pack and checkpoint signoff docs.
4. Sweep runtime queue/heartbeat gates and lock closeout snapshot.
5. Start next implementation batch with same WIP and gate discipline.

## Daily control gates
- pending stale (24h+): must be 0
- stale heartbeats (1h+): must be <= 2
- queued runtime requests: must be <= 3
- wave03 issue close rate: must be 3/3 by sprint closeout

## Active source of truth
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/control_snapshot_2026-02-18.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/queue_recovery_2026-02-18.ndjson
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2_RELAUNCH_DISPATCH_2026-02-18.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_QA_EVIDENCE_PACK_2026-02-19.md
