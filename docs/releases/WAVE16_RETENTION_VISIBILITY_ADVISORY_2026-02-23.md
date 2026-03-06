# Wave16 Retention Visibility Advisory (2026-02-24 checkpoint)

## Objective
Maintain Wave16 advisory lane in event-driven mode with operator-first digest, evidence-backed recommendations, and one deep research item per phase touchpoint.

## Brief 60s
- On est ou: phase is Ship; codex-only guard is active; new Wave16 runtime checkpoint and dispatch artifacts are available.
- On va ou: keep dual-root pulse/check cadence and credit guard until Feb 26 while AG lane stays paused.
- Pourquoi: retention status is still warn/overdue, and stale cadence can reduce operator trust.
- Comment: checkpoint only on material delta, then publish short action-first rows with owner/action/evidence/decision.

## Retention visibility (owner/next_action/evidence/decision_tag)
- status: warn
- policy_version: wave14-7-30-90-permanent-v1
- generated_at: 2026-02-23T10:27:53+00:00
- next_compaction_at: 2026-02-23T12:27:53+00:00
- totals: hot_7d=81 warm_30d=109 cool_90d=0 archive_permanent=0
- owner: @victor
- next_action: run manual retention refresh now, then republish status with evidence.
- evidence_path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
- decision_tag: defer

## Recommendations (3 operator rows)
- R1 | recommendation: restore retention freshness before next operator decision window. | owner:@victor | next_action: regenerate retention_status and confirm next_compaction_at is in the future. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json | decision_tag:adopt
- R2 | recommendation: keep dual-root recency cadence under credit guard. | owner:@victor | next_action: execute pulse/check loop every 30-45 min and append proof in Wave16 runtime checkpoint logs. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/docs/releases/WAVE16_RUNTIME_CHECKPOINT_2026-02-24T1031Z.md | decision_tag:adopt
- R3 | recommendation: keep operator trust wording explicit for codex-only isolation. | owner:@clems | next_action: keep codex-only and AG pause wording in operator updates until credits are restored. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md | decision_tag:adopt

## Deep RnD D1 (phase-mapped)
- D1 | recommendation: retention confidence scorecard from freshness lag + totals stability + checkpoint latency.
- owner: @nova
- next_action: validate scorecard against three Wave16 artifacts (runtime checkpoint, dispatch guard, push receipt) and record false-alert rate.
- evidence_path:
  - /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WAVE16_RUNTIME_CHECKPOINT_2026-02-24T1031Z.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_PUSH_RECEIPT_2026-02-24.md
- decision_tag: defer

## Now/Next/Blockers
- Now: event-driven Wave16 checkpoint published on material delta (new 2026-02-24 run artifacts).
- Next: publish next checkpoint only when retention/run/blocker/phase delta appears.
- Blockers: none.

## Blocker escalation (>60 min)
- Option A: freeze new lane changes and keep codex-only maintenance until blocker clears.
- Option B: proceed with limited lane work under manual overrides.
- Recommended: Option A.
- Ping: @clems

## Evidence paths
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
- /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WAVE16_RUNTIME_CHECKPOINT_2026-02-24T1031Z.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_PUSH_RECEIPT_2026-02-24.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md
