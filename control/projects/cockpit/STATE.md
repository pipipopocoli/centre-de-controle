# State

## Phase
- Ship

## Objective
- Execute WAVE05 ENHANCED: registry runtime + scoring dispatch + fallback chain + CAD cost + SLO gates.

## Now
- Wave05 backend contracts locked on dispatch/router lane.
- Strict provider chain active: codex -> antigravity -> ollama (flagged by `ollama_enabled`).
- Cost telemetry schema v2 active in `runs/cost_events.ndjson` (backward compatible keys preserved).
- Backend verification suite green.
- `verify_project_bible` green via `.venv` run.
- Runtime gates green: pending=0 and stale_heartbeats_gt1h=0.

## Next
- Operator signoff and merge/ship handoff.
- Keep 60m gate recheck cadence until release confirmation.

## In Progress
- none

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
