# State

## Phase
- Implement

## Objective
- Ship Wave11: Dev Live clarity, vulgarisation freshness proof, and full snapshot push.

## Now
- Runtime panel now states Dev Live behavior explicitly, including expected two-icon behavior.
- Vulgarisation renders with generated_at, freshness status, runtime source, root path, and file proof paths.
- Pilotage health line now includes runtime source and vulgarisation freshness/generated timestamp.
- AppSupport remains canonical runtime root for active desktop usage.
- Wave10 lanes remain tracked while Wave11 clarity closeout is integrated.

## Next
- Run Wave11 smoke suite before push.
- Publish push manifest and push receipt with SHA + refs.
- Push snapshot branch then main.
- Keep dual-root cadence checks every 30-45 minutes during wave execution.

## In Progress
- ISSUE-CP-0039-wave10-chat-incremental-scroll-lock
- ISSUE-CP-0040-wave10-refresh-decoupling-performance
- ISSUE-CP-0041-wave10-ui-click-context-routing
- ISSUE-CP-0043-wave10-throughput-burst-governance
- WAVE11 dev-live clarity closeout + snapshot push lane

## Blockers
- none

## Deferred debt
- ISSUE-CP-0015 remains deferred and non-blocking.

## Risks
- operator confusion if stale release app is launched instead of Dev Live.
- stale_tick can return if cadence pulses are skipped.
- full snapshot push increases blast radius if smoke gate is skipped.

## Gates
- pending_stale_gt24h == 0
- stale_heartbeats_gt1h <= 2
- queued_runtime_requests <= 3
- repo_root_healthcheck == healthy
- appsupport_root_healthcheck == healthy
- tournament_auto_dispatch == false

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE10_DISPATCH_2026-02-22.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE11_DISPATCH_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE11_PUSH_MANIFEST_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE11_PUSH_RECEIPT_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0039-wave10-chat-incremental-scroll-lock.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0040-wave10-refresh-decoupling-performance.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0041-wave10-ui-click-context-routing.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0042-wave10-vulgarisation-clean-simple-tech.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0043-wave10-throughput-burst-governance.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/PACKAGING.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/RUNBOOK.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md
