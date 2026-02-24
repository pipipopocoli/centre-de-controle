# Decisions

## 2026-02-13 - ADR-CP-001 Wave execution for big checkpoint
- Status: Accepted
- Context: We need a large multi-agent push, but OS rule requires WIP <= 5.
- Decision: Run checkpoint CP-01 in two waves. Wave 1 starts now with 5 active issues; Wave 2 starts after Wave 1 merge and smoke.
- Rationale: Keeps delivery fast without turning merge/test into chaos.
- Consequences: Better stability and ownership clarity; small delay for queued items.
- Owners: clems, victor, leo
- References: CHECKPOINT_GROS_PUSH_2026-02-13.md, STATE.md

## 2026-02-13 - ADR-CP-002 Delegation map by lead
- Status: Accepted
- Context: Victor and Leo need immediate task packs to dispatch to specialists.
- Decision: Backend lane delegated by @victor to `@agent-1`..`@agent-5`; UI lane delegated by @leo to `@agent-6`..`@agent-10`.
- Rationale: Avoid overlap, enforce single owner per issue, speed up throughput.
- Consequences: More parallel output, but requires strict status reporting cadence.
- Owners: clems, victor, leo
- References: missions/MISSION-VICTOR-CHECKPOINT-CP1.md, missions/MISSION-LEO-CHECKPOINT-CP1.md

## 2026-02-19 - ADR-CP-003 Wave04 parallel chain model
- Status: Accepted
- Context: Wave03 is closed, and next cycle needs higher throughput without losing runtime control.
- Decision: Run Wave04 with 5 parallel chains (C0-C4) and hard WIP cap of 5.
- Rationale: Maximizes parallelism while preserving single owner accountability.
- Consequences: Faster progress with strict gate discipline; requires regular heartbeat/control checks.
- Owners: clems, victor, leo
- References: PAPER_PLAN_WAVE04_PARALLELIZATION_MAX_2026-02-19.md, runs/WAVE04_GATE_CHECKLIST_2026-02-19.md

## 2026-02-19 - ADR-CP-004 Tournament dormant guard during Wave04
- Status: Accepted
- Context: Tournament assets must remain reusable but cannot block active implementation.
- Decision: Keep tournament trees intact and dormant; no auto-dispatch, no auto-judge.
- Rationale: Preserve capability without introducing scope collision.
- Consequences: Tournament remains available by manual operator activation only.
- Owners: clems
- References: docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md, ROADMAP.md

## 2026-02-19 - ADR-CP-005 Wave05 enhanced runtime stack
- Status: Accepted
- Context: Cockpit V2 needs runtime flexibility and better operator control without breaking current stability.
- Decision: Implement Wave05 with 5 locked upgrades: registry runtime source of truth, deterministic scoring dispatch, 3-tier provider fallback, CAD cost telemetry, and SLO GO/HOLD gates.
- Rationale: Removes hardcode friction, improves dispatch quality, and gives clear operation signals before ship decisions.
- Consequences: New settings blocks and runtime artifacts added; fallback remains feature-flagged for Ollama.
- Owners: clems, victor, leo
- References: control/projects/cockpit/issues/ISSUE_MAP_WAVE05_CP003X.md, control/projects/cockpit/runs/V2_WAVE05_DISPATCH_2026-02-19.md

## 2026-02-19 - ADR-CP-006 Cleanup canonical lock (spec/env/docs)
- Status: Accepted
- Context: Cleanup scope had duplicate candidates for build spec, virtualenv path, and V2 docs source-of-truth, creating operator ambiguity and cleanup risk.
- Decision: Lock cleanup canonicals to `Centre de controle.spec`, `.venv/`, and docs source-of-truth split as `docs/reports/` (ops evidence) plus `tournament-v1/` and `tournament-v2/` (tournament evidence). Keep tournament trees and related arena/ops paths under hard exclusion in cleanup passes.
- Rationale: One canonical set reduces drift and prevents accidental destructive actions on reusable tournament assets.
- Consequences: `cockpit.spec` and `cockpit_v5.spec` are legacy/non-canonical references; `venv/` is fallback-only; root `Cockpit_V2_*.pdf` files are archive references, not primary operational source-of-truth.
- Owners: clems, agent-11
- References: docs/reports/BACKLOG_CLEANUP_V2.md, docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md, control/projects/cockpit/issues/ISSUE-CP-0024-wave04-cleanup-canonicalization.md

## 2026-02-19 - ADR-CP-007 Wave06 closeout gate
- Status: Accepted
- Context: Wave06 introduced Nova L1 plus hybrid timeline and needed an explicit closeout gate before the next wave.
- Decision: Lock Wave06 as GREEN after verification suite pass and runtime gate recheck (pending/queued/stale all green).
- Rationale: Prevents partial handoff and keeps implementation quality traceable.
- Consequences: Wave06 scope is frozen; follow-up work moves to Wave07 hardening lanes.
- Owners: clems, victor, leo, nova
- References: runs/WAVE06_CLOSEOUT_2026-02-19.md, runs/WAVE06_BACKEND_SHIP_READINESS_2026-02-19T1728Z.md

## 2026-02-19 - ADR-CP-008 Wave07 hardening launch
- Status: Accepted
- Context: After Wave06 closeout, remaining risk is in contract hardening and operator readability at scale.
- Decision: Launch Wave07 with three lanes: backend hardening (@victor), UI polish (@leo), advisory loop (@nova), under WIP<=5 and 2h cadence.
- Rationale: Parallel lanes maximize throughput without losing control discipline.
- Consequences: New dispatch packet is canonical for this cycle; tournament remains dormant.
- Owners: clems, victor, leo, nova
- References: runs/V2_WAVE07_DISPATCH_2026-02-19.md, STATE.md, ROADMAP.md

## 2026-02-20 - ADR-CP-009 Wave08 runtime parity + closeout lock
- Status: Accepted
- Context: Wave07 remained blocked by false degraded signals from stale runtime tick semantics and unresolved UI evidence status.
- Decision: Run Wave08 with strict priority order: runtime parity fix first, UI closeout second, Nova advisory lock third.
- Rationale: Removes noisy degraded alerts, restores operator trust in health signals, and closes remaining ship blockers.
- Consequences: Healthcheck now consumes reconciled runtime view and activity-aware stale detection; `CP-0034` is closed with finalized evidence.
- Owners: clems, victor, leo, nova
- References: scripts/auto_mode_healthcheck.py, app/services/auto_mode.py, issues/ISSUE-CP-0034-wave07-ui-polish.md, docs/reports/CP01_UI_WAVE07_EVIDENCE.md

## 2026-02-20 - ADR-CP-010 Wave09 dual-root cadence lock
- Status: Accepted
- Context: After Wave08 closeout, runtime can still fall back to degraded over time when dual-root activity cadence is not maintained, especially on AppSupport KPI snapshot recency.
- Decision: Launch Wave09 with a two-layer model: P0 dual-root cadence lock (repo + AppSupport required green), then P1/P2 implementation lanes (healthcheck hardening, Pilotage visibility, Nova advisory lock).
- Rationale: Keeps control gates trustworthy while continuing delivery without introducing tournament or architecture scope drift.
- Consequences: New issue set CP-0035..CP-0038 opened, Wave09 dispatch packet becomes canonical, and dual-root health is now a mandatory continuation gate.
- Owners: clems, victor, leo, nova
- References: runs/WAVE09_PRECHECK_2026-02-20.md, runs/V2_WAVE09_DISPATCH_2026-02-20.md, ROADMAP.md, STATE.md

## 2026-02-20 - ADR-CP-011 Nova dual mandate (vulgarisation + scientific RnD)
- Status: Accepted
- Context: Nova was active mainly as vulgarisation advisor, while Cockpit now needs a persistent creative-science scouting lane for code, literature, and technology updates.
- Decision: Encode Nova as a dual-mandate L1 role: operator vulgarisation plus deep scientific RnD scouting with phase-by-phase prompt cadence and decision ledger.
- Rationale: Preserves operator clarity while continuously injecting high-value research into implementation decisions.
- Consequences: Nova persona, registry skills, and mission templates are updated; each checkpoint must include one deep RnD item with owner/action/evidence and adopt/defer/reject tag.
- Owners: clems, nova
- References: agents/nova.md, control/projects/cockpit/agents/registry.json, control/projects/cockpit/missions/MISSION-NOVA-WAVE09-RESEARCH.md

## 2026-02-20 - ADR-CP-012 Message-driven Wave09 execution order
- Status: Accepted
- Context: Latest messages confirm Nova Wave09 kickoff and identify CP-0035 as P0 to eliminate cadence-related false degraded behavior before deeper lanes.
- Decision: Adopt Nova P0 recommendation and lock execution order as `CP-0035 -> CP-0036 (parallel) -> CP-0037 -> CP-0038`.
- Rationale: Keeps runtime control trustworthy first, then enables UI/advisory closeout on stable gates.
- Consequences: UI lane starts after first backend green checkpoint; operational cadence checks remain mandatory every 30-45 minutes.
- Owners: clems, victor, leo, nova
- References: runs/WAVE09_DECISION_2026-02-20T2148Z.md, runs/V2_WAVE09_DISPATCH_2026-02-20.md, runs/WAVE09_PRECHECK_2026-02-20.md

## 2026-02-20 - ADR-CP-013 Leo lane activation after message review
- Status: Accepted
- Context: Latest Leo status confirms UI lane independence and no blockers, but no Wave09 closeout evidence yet.
- Decision: Move CP-0037 to `In Progress` and enforce closeout contract (badges + matrix + mapped screenshots, including degraded case).
- Rationale: Keeps momentum from Leo ack while preserving a verifiable finish gate.
- Consequences: Leo lane is active now, but cannot move to Done without evidence artifacts.
- Owners: clems, leo
- References: runs/WAVE09_LEO_DECISION_2026-02-20T2150Z.md, issues/ISSUE-CP-0037-wave09-pilotage-control-badges.md, missions/MISSION-LEO-WAVE09.md

## 2026-02-21 - ADR-CP-014 Desktop update channel lock (Dev Live vs Release)
- Status: Accepted
- Context: Operator needs predictable update behavior and clear distinction between live repo iteration and packaged snapshot behavior.
- Decision: Lock two explicit desktop channels:
  1. Dev Live (`./launch_cockpit.sh`) is source of truth during implementation.
  2. Release app (`dist/Centre de controle.app`) is a frozen snapshot that requires explicit rebuild.
- Rationale: Prevents version confusion and false assumption of packaged auto-update.
- Consequences: Runtime context panel now exposes mode and runtime root; docs include one-command installer for a Dev Live Dock launcher.
- Owners: clems, victor, leo
- References: docs/PACKAGING.md, docs/RUNBOOK.md, scripts/packaging/install_dev_live_launcher.sh, app/ui/sidebar.py, app/main.py

## 2026-02-22 - ADR-CP-015 Wave10 UX lock (chat + context + vulgarisation)
- Status: Accepted
- Context: Wave09 closed runtime gates, but operator UX still had three blockers: chat jump, dense vulgarisation, and missing click-driven context for dispatch.
- Decision: Launch Wave10 with five scoped issues CP-0039..CP-0043, lock lead-first execution, and keep balanced throughput (`auto_mode.max_actions=2`) under existing backpressure gates.
- Rationale: Improves operator speed and clarity without reopening architecture risk.
- Consequences: Chat updates are incremental, context payload is explicit in chat/request flow, vulgarisation supports simple/tech modes, and cadence hygiene remains mandatory.
- Owners: clems, victor, leo, nova
- References: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0039-wave10-chat-incremental-scroll-lock.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0040-wave10-refresh-decoupling-performance.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0041-wave10-ui-click-context-routing.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0042-wave10-vulgarisation-clean-simple-tech.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0043-wave10-throughput-burst-governance.md

## 2026-02-23 - ADR-CP-016 Wave11 Dev Live clarity + vulgarisation trust proof
- Status: Accepted
- Context: Operator reported confusion from seeing two app icons in Dock and uncertainty about whether vulgarisation was updated.
- Decision: Keep Dev Live as default channel and explicitly document/show that two icons are expected (launcher + python runtime). Add runtime source and freshness proof in vulgarisation and pilotage.
- Rationale: Removes operator ambiguity without changing the chosen Dev Live workflow.
- Consequences: Sidebar, Pilotage, and Vulgarisation expose source root, generated_at, and freshness status. AppSupport remains canonical runtime source.
- Owners: clems, victor, leo, nova
- References: /Users/oliviercloutier/Desktop/Cockpit/app/ui/sidebar.py, /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py, /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py, /Users/oliviercloutier/Desktop/Cockpit/docs/PACKAGING.md, /Users/oliviercloutier/Desktop/Cockpit/docs/RUNBOOK.md

## 2026-02-23 - ADR-CP-017 Wave12.1 closeout + Wave13 UX lock
- Status: Accepted
- Context: After Wave11 push, operator still reported three UX gaps: weak hierarchy readability, dense vulgarisation simple mode, and missing compact live progress visibility.
- Decision: Close Wave12.1 first (push canonical isolation/runtime clarity changes), then launch Wave13 with four scoped issues: CP-0044 (L0/L1/L2 hierarchy), CP-0045 (simple vulgarisation cleanup), CP-0046 (live task+code+agent view), CP-0047 (pulse recency stability signal).
- Rationale: Keeps delivery momentum while resolving operator-facing pain points without architecture rewrite.
- Consequences: New live activity feed service and updated Pilotage/Overview contracts; cadence trust includes explicit pulse signal; tournament remains dormant.
- Owners: clems, victor, leo, nova
- References: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE12_PUSH_RECEIPT_2026-02-23.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0044-wave13-agent-hierarchy-l0-l1-l2.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0045-wave13-vulgarisation-simple-clean.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0046-wave13-live-view-task-code-hybrid.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0047-wave13-runtime-cadence-stability.md

## 2026-02-23 - ADR-CP-018 Wave14 lock from cockpit_v2_final_plan.docx
- Status: Accepted
- Context: Operator provided a consolidated Word document with direct answers on functional criteria, autonomy boundaries, priorities, role model, memory retention, and quality gates.
- Decision: Use `/Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx` as Wave14 intent source and translate it into five execution issues: CP-0048..CP-0052.
- Rationale: Removes ambiguity and aligns implementation lanes with explicit operator intent.
- Consequences: Wave14 prioritizes startup onboarding, mission-critical gate, false-positive hardening, live readability, and retention policy before new feature expansion.
- Owners: clems, victor, leo, nova
- References: /Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx, /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_INPUT_FROM_COCKPIT_V2_FINAL_PLAN_2026-02-23.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE14_DISPATCH_2026-02-23.md

## 2026-02-24 - ADR-CP-019 Wave16 codex-only outage and credit guard
- Status: Accepted
- Context: Antigravity is unavailable and remaining credits must be preserved until Feb 26 without freezing core backend/advisory delivery.
- Decision: Execute Wave16 in codex-only mode (`victor`, `nova`, optional `agent-3`) with an explicit outage policy in settings and dispatch enforcement in auto-mode. Apply credit guard with effective action cap = 1, wave cap <=180, reserve floor >=350.
- Rationale: Keeps delivery moving while avoiding AG dependency and uncontrolled burn.
- Consequences: Leo/UI expansion lane is paused; AG-targeted requests are closed with explicit outage reason during this window; dual-root pulse/check cadence becomes mandatory to avoid stale-only degraded drift.
- Owners: clems, victor, nova
- References: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE16_CP0056_CP0060.md, /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json, /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py, /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_codex_only_outage_mode.py
