# State

## Phase
- Ship

## Objective
- Reopen AG under credit guard (max_actions_effective=1), keep dual-root runtime healthy, and keep lead-first dispatch deterministic.

## Now
- Wave17 outage policy: allow AG under guard (`allowed_platforms=[codex,antigravity]`, `allowed_agents=[victor,nova,leo,agent-3]`).
- Credit guard remains enabled (`wave_cap <= 180`, `reserve_floor >= 350`, `max_actions_effective=1`).
- Wave17 dual-root checkpoint is healthy (repo + AppSupport).
- Recency autopulse guard and onboarding contract tests are green.
- Agent heartbeats refreshed (UI no longer stale).
- Public site republished to production (`cockpit-v2-launch`) with Wave16 explainer and diagrams/charts.
- Lead-first dispatch policy stays active (`@victor` -> `@nova` -> wait -> optional `@agent-3`; `@leo` allowed under guard).
- Primary operator app icon switched to single-icon release target (`/Applications/Centre de controle.app`).

## Next
- Keep pulse/check cadence on both roots every 30-45 minutes.
- Enforce credit guard (`wave_cap <= 180`, `reserve_floor >= 350`).
- Keep fanout closed until 2 consecutive healthy dual-root checkpoints.
- Track operator usage on release single-icon path and keep Dev Live optional only.

## In Progress
- none

## Blockers
- none

## Deferred debt
- none

## Risks
- stale recency warnings drift back if pulse cadence is not respected.
- dual-root settings drift (repo vs AppSupport) can create dispatch confusion.
- credits can burn too quickly if specialist fanout is reopened too early.

## Gates
- pending_stale_gt24h == 0
- stale_heartbeats_gt1h <= 2
- queued_runtime_requests <= 3
- repo_root_healthcheck == healthy
- appsupport_root_healthcheck == healthy
- outage_mode_guard == allow_ag_under_guard
- credit_reserve_floor_reached == false
- tournament_auto_dispatch == false

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE17_RUNTIME_CHECKPOINT_2026-02-27T0539Z.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0015_CP0042_CLOSEOUT_2026-02-23T0909Z.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE14_VICTOR_LANE_LOCK_2026-02-23T1026Z.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_CP0050_MEMORY_RETENTION_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/WAVE14_UI_EVIDENCE_MAPPING.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_CLOSEOUT_RECEIPT_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_OPERATOR_RECENCE_RUNBOOK_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_INPUT_FROM_COCKPIT_V2_FINAL_PLAN_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE14_DISPATCH_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0048-wave14-startup-pack-existing-repo-onboarding.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0049-wave14-mission-critical-commit-gate.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0050-wave14-memory-retention-policy.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0051-wave14-live-task-squares-and-timeline-clarity.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0052-wave14-healthcheck-zero-false-positive.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0053-wave15-dual-root-recency-lock.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0054-wave15-wave14-closeout-sync.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0055-wave15-operator-recence-runbook.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE16_CP0056_CP0060.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0056-wave16-codex-only-outage-mode.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0057-wave16-dirty-tree-consolidation-push.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0058-wave16-credit-guard-dispatch-policy.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0059-wave16-dual-root-recence-ops-cadence.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0060-wave16-nova-retention-operator-digest.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_BACKEND_ONBOARDING_RECENCY_2026-02-23T1318Z.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE16_RETENTION_VISIBILITY_ADVISORY_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_OPERATOR_RECENCY_RUNBOOK_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_PUSH_RECEIPT_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WEB_REPUBLISH_WAVE16_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/scripts/packaging/install_release_app.sh
- /Users/oliviercloutier/Desktop/Cockpit/docs/PACKAGING.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/RUNBOOK.md
