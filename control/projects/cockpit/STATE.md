# State

## Phase
- Implement

## Objective
- Execute WAVE05 ENHANCED: registry runtime + scoring dispatch + fallback chain + CAD cost + SLO gates.

## Now
- Core patches started on `store`, `auto_mode`, `execution_router`, `project_bible`, `project_pilotage`.
- Wave05 issue map opened (CP-0026..CP-0032).
- Agent mission pack and dispatch copy created.
- Tournament capability kept dormant (manual trigger only).

## Next
- Run Wave05 verification tests and close regressions.
- Lock Gate 1: registry + fallback + telemetry artifacts.
- Lock Gate 2: scoring/backpressure + UI SLO/cost visibility.

## In Progress
- C0 control cadence / runtime hygiene
- C1 registry runtime (CP-0026/0027)
- C2 scoring + backpressure (CP-0028/0029)
- C3 router fallback + cost telemetry (CP-0030/0031)
- C4 SLO gates + UI evidence (CP-0032)

## Blockers
- none

## Risks
- dispatch regression if registry and fallback paths diverge
- false GO/HOLD if SLO verdict lacks enough latency samples
- cost estimate drift if provider rates stay default too long

## Gates
- pending_stale_gt24h == 0
- stale_heartbeats_gt1h <= 2
- queued_runtime_requests <= 3
- wave05_issue_map_opened == true
- tournament_auto_dispatch == false

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE05_CP003X.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE05_DISPATCH_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE05.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-LEO-WAVE05.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md
