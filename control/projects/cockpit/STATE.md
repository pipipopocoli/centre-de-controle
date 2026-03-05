# State

## Phase
- Ship

## Objective
- Ship Wave21 API-native operations: OpenRouter model routing, agentic chat/scene turns, voice STT, Pixel View, and Android bootstrap aligned to cloud API.

## Now
- Wave20R release-hardening branch is active on `codex/wave20r-release-hardening` (resynced from `origin/main`).
- Wave20R control snapshot is clean (`rows_open=0`, `invalid_action=0`, `defer_missing_reason=0`) via strict control-tower run.
- Technical gates are green: `python -m py_compile`, desktop `npm lint`, desktop `npm build`, `cargo check` (core + tauri).
- Target verification tests passed: `tests/verify_hybrid_timeline.py`, `tests/verify_timeline_feed.py`, `tests/verify_execution_router.py`.
- Policy gate scan found unresolved production debt (`owner123!`, absolute local paths in scripts, legacy provider runtime references in active services).
- Wave17 outage policy remains guarded (`allowed_platforms=[codex,antigravity]`, `allowed_agents=[victor,leo,nova,vulgarisation]`).
- Credit guard remains enabled (`wave_cap <= 180`, `reserve_floor >= 350`, `max_actions_effective=1`).
- Wave17 dual-root checkpoint is healthy (repo + AppSupport).
- Recency autopulse guard and onboarding contract tests are green.
- Wave20 strict Wizard schema is locked (`additionalProperties=false`, strict required fields, L1 exact).
- Wave20 runtime default backend is API (`COCKPIT_RUNTIME_BACKEND=api`) with startup health gate on `/healthz`.
- Local destructive boot cleanup is disabled by default and requires explicit env opt-in (`COCKPIT_ENABLE_BOOT_CLEANUP=1`).
- Agent roster now includes `vulgarisation` as L1 lead under `clems`.
- Public site republished to production (`cockpit-v2-launch`) with Wave16 explainer and diagrams/charts.
- Lead-first dispatch policy stays active (`@victor` -> `@nova` -> wait; `@leo` allowed under guard).
- Wave18 Takeover Wizard is available (UI button + `#wizard` trigger) and writes BMAD + run logs into the project dir.
- Wave19 Wizard Live is available (`#wizard-live start|run|stop`) with session mode and one headless bundled run per operator turn.
- Wizard Live auto-kickoff is enabled after `New Project` and after takeover success (no popup).
- Auto-send toggle is opt-in in Auto-mode panel (paste+enter via AppleScript; permissions may be required).
- Primary operator app icon switched to single-icon release target (`/Applications/Centre de controle.app`).
- Cloud API-first foundation scaffolded (`server/`) for Desktop + Android parity, with RBAC/JWT, REST contracts, WS event envelope, and wizard-live endpoints.
- Telegram/WhatsApp are explicitly excluded from the V1 execution scope.
- Wave21 endpoints are live for model routing and agentic runtime (`/llm-profile`, `/chat/agentic-turn`, `/voice/transcribe`, `/pixel-feed`).
- Desktop now exposes `Model Routing` and `Pixel View` tabs, plus `Vocal` and `Scène` actions in chat.
- OpenRouter runtime defaults are wired (`gemini-2.5-flash` STT, `lfm-2.5-thinking` L1, `trinity-large-preview` L2 scene) with LFM spawn cap 10.
- Android native bootstrap module exists under `/android` with Compose entrypoint and Retrofit API skeleton.

## Next
- Remove hardcoded default credentials from active source (`app/services/cloud_api_client.py`, seed in `server/repository.py`).
- Remove user-specific absolute paths from active scripts under `/scripts`.
- Complete OpenRouter-only cleanup in active runtime paths (`app/services/*`, `app/data/store.py`, `app/services/execution_router.py`, registry defaults).
- Re-run policy gates on active source after cleanup and lock release checklist for PR.
- Run 1 full Wave19/Wave20 live session on a real repo and confirm repeated turns stay stable with L1=4.
- Validate strict API startup paths (down => hard fail, up => strict write blocks on local UI actions).
- Finish desktop API-client cutover to remove remaining local legacy flows.
- Start Android native client implementation against `/v1/*` + `WS /v1/projects/{id}/events`.
- Implement Android parity screens + websocket live sync + FCM worker wiring (post-bootstrap).
- Complete AppSupport drift cleanup by moving evozina intake artifacts out of cockpit root.
- Keep pulse/check cadence on both roots every 30-45 minutes.
- Enforce credit guard (`wave_cap <= 180`, `reserve_floor >= 350`).
- Keep fanout closed until 2 consecutive healthy dual-root checkpoints.
- Track operator usage on release single-icon path and keep Dev Live optional only.

## In Progress
- none

## Blockers
- `starlette` (and related API test deps) missing in current Python env; cloud API route tests cannot run until env is completed.
- `scripts/wave20r_control_tower.py` is not present on `main`; strict run currently relies on snapshot copy from archived branch.

## Deferred debt
- none

## Risks
- stale recency warnings drift back if pulse cadence is not respected.
- dual-root settings drift (repo vs AppSupport) can create dispatch confusion.
- credits can burn too quickly if specialist fanout is reopened too early.
- release can regress security posture if policy debt (`owner123!`, absolute paths, legacy providers) is not closed before merge.

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
- /Users/oliviercloutier/Desktop/Cockpit/docs/TAKEOVER_WIZARD.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/WIZARD_LIVE.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/OPENROUTER_SETUP.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/PIXEL_VIEW.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/CLOUD_API_PROTOCOL.md
- /Users/oliviercloutier/Desktop/Cockpit/android/README.md
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
