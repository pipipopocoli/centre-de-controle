# State

## Phase
- Implement

## Objective
- Ship Wave13 UX lock: L0/L1/L2 hierarchy, live view task+code, clean vulgarisation simple mode, and pulse recency clarity.

## Now
- Wave12.1 closeout pushed to `main` with receipt and canonical cockpit isolation lock.
- Overview agent grid now renders explicit hierarchy sections L0/L1/L2 with action/attente/bloque/repos counts.
- Pilotage now shows a compact live view (`Code now`, `Tasks now`, `Agents now`) with linked-repo-first fallback.
- Vulgarisation simple mode has reduced density: 4 brief blocks + What next + Timeline focus.
- Runtime cadence now tracks `last_pulse_at` and exposes pulse status in health signals.

## Next
- Validate visual quality in desktop app (live run) and collect screenshot evidence for Wave13 lanes.
- Dispatch lead prompts (@victor/@leo/@nova), then specialists after T+15m ack.
- Keep dual-root cadence checks every 30-45 min during active lanes.
- Close CP-0044..CP-0047 with mapped QA evidence.

## In Progress
- ISSUE-CP-0044-wave13-agent-hierarchy-l0-l1-l2
- ISSUE-CP-0045-wave13-vulgarisation-simple-clean
- ISSUE-CP-0046-wave13-live-view-task-code-hybrid
- ISSUE-CP-0047-wave13-runtime-cadence-stability

## Blockers
- none

## Deferred debt
- ISSUE-CP-0015 remains deferred and non-blocking.

## Risks
- visual hierarchy can still feel dense if card content is too long.
- stale pulse can return if cadence checks are skipped in long inactive windows.
- linked repo can be unset for some projects (fallback expected).

## Gates
- pending_stale_gt24h == 0
- stale_heartbeats_gt1h <= 2
- queued_runtime_requests <= 3
- repo_root_healthcheck == healthy
- appsupport_root_healthcheck == healthy
- tournament_auto_dispatch == false

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE12_PUSH_RECEIPT_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0044-wave13-agent-hierarchy-l0-l1-l2.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0045-wave13-vulgarisation-simple-clean.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0046-wave13-live-view-task-code-hybrid.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0047-wave13-runtime-cadence-stability.md
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/agents_grid.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/live_activity_feed.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
