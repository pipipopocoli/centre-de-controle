# Memory - nova

## Role
- Operate dual lane advisory:
  - lane A: operator-first vulgarisation.
  - lane B: creative-science RnD scouting.
- Convert state signals into owner-routed recommendations with evidence and decision tags.

## Facts / Constraints
- Current wave focus: CP-0042 vulgarisation clean split (`simple` + `tech`).
- `simple` must stay readable in <=60s and action-first.
- `tech` must keep full evidence tables.
- Recommendation contract: owner + next_action + evidence_path + decision_tag.
- Reporting cadence: `Now/Next/Blockers` every 2h.

## Wave10 CP-0042 Closeout
- Brief 60s
  - On est ou: Wave10 is Implement; simple/tech contract is active in service and UI.
  - On va ou: lock CP-0042 closeout and keep CP-0036/dual-root hygiene stable while other Wave10 lanes continue.
  - Pourquoi: operator clarity drops fast if simple mode is noisy or if recommendations are missing owner/action/evidence/decision.
  - Comment: keep simple concise, keep tech complete, and enforce recommendation rows with explicit decision tags.
- Recommendation ledger
  - R1 | decision_tag:adopt | owner:@nova | next_action:keep recommendation table active in simple and tech rendering paths | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
  - R2 | decision_tag:defer | owner:@victor | next_action:close CP-0036 stale semantics lock before raising stricter freshness thresholds | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
  - R3 | decision_tag:reject | owner:@clems | next_action:keep tournament auto-dispatch disabled during active implementation lanes | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- Deep RnD item (current phase)
  - D1 | decision_tag:adopt | recommendation:Adaptive readability budget for Simple mode using comprehension guardrails. | owner:@nova | next_action:run a small matrix that compares <=60s simple summaries against tech detail and keep comprehension gate >=0.85. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py

## Now
- CP-0042 lane is closure-ready with simple action-first and tech evidence-complete rendering.

## Next
- Keep 2h status cadence in `Now/Next/Blockers`.
- Monitor recommendation rows in live refreshes and keep one deep RnD item per phase.

## Blockers
- none

## Wave11 trust advisory
- Brief 60s
  - On est ou: Wave11 active; Dev Live clarity explicit; AppSupport is canonical runtime root.
  - On va ou: complete smoke + push manifest/receipt with gates green.
  - Pourquoi: trust drops when mode/root/freshness verification is ambiguous.
  - Comment: run canonical 4-point check before action, then execute evidence-first.
- Checklist - canonical cockpit verification
  - mode: Dev Live
  - project_id: cockpit
  - runtime_root: AppSupport canonical root
  - freshness_timestamp: generated_at=2026-02-20T17:21:10+00:00
- Residual risks top 3
  - R1 | risk: stale release launch confusion | owner:@leo | action: keep Dev Live anti-confusion text + cue | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
  - R2 | risk: stale_tick return if cadence pulses are skipped | owner:@victor | action: keep cadence checks every 30-45 min | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
  - R3 | risk: larger blast radius if smoke gate is skipped before push | owner:@clems | action: enforce smoke suite + push receipt refs | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- Deep RnD D1
  - D1 | recommendation: trust-score rubric for mode/root/freshness/operator proof. | owner:@nova | next_action: draft 4-signal rubric and validate on 3 live refresh cycles. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md | decision_tag:adopt
- Cadence: publish `Now/Next/Blockers` every 2h.

## Wave14 CP-0050 retention closeout
- Brief 60s
  - On est ou: CP-0050 retention policy is enforced in memory indexing with status artifact written at each build.
  - On va ou: keep manual 2h cadence and run next compaction checkpoint from retention_status.json.
  - Pourquoi: keep operator trust and audit trail without destructive purge or cross-project leak.
  - Comment: apply tiered ingest only (7d/30d/90d) and archive >90d or invalid timestamps as permanent gzip artifacts.
- Operator wording pass (@agent-11)
  - 7d hot / 30d warm / 90d cool / >90d permanent archive.
  - Action: run memory index build, verify retention_status, then post Now/Next/Blockers.
- Retention status snapshot
  - policy_version: wave14-7-30-90-permanent-v1
  - generated_at: 2026-02-23T10:27:53+00:00
  - next_compaction_at: 2026-02-23T12:27:53+00:00
  - totals: hot_7d=80 warm_30d=109 cool_90d=0 archive_permanent=0
- Deep RnD D1
  - D1 | recommendation: retention confidence score from timestamp quality + tier coverage. | owner:@victor | next_action:add deterministic tests for timestamp_missing/invalid/old rows and track confidence in retention_status.json. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json | decision_tag:adopt
- Now/Next/Blockers (2h cadence)
  - Now: retention enforcement active and isolation preserved for cockpit.
  - Next: run next compaction checkpoint at 2026-02-23T12:02:32+00:00 and monitor archive_permanent counts.
  - Blockers: none.

## Wave15 operator recency runbook
- Brief 60s
  - On est ou: dual-root recency lock is active and stale snapshot can be warning-only when pulse is fresh.
  - On va ou: keep both roots healthy through cadence checkpoints and close Wave15 governance issues.
  - Pourquoi: avoid false operational noise while preserving true runtime failures.
  - Comment: run pulse then healthcheck on both roots every 30-45 minutes.
- Advisory ledger
  - R1 | decision_tag:adopt | owner:@victor | next_action:keep stale tick and pulse stale as blocking errors; keep stale snapshot soft only when pulse is fresh. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py
  - R2 | decision_tag:adopt | owner:@clems | next_action:publish closeout receipt with dual-root health snapshots and test results. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_CLOSEOUT_RECEIPT_2026-02-23.md
  - R3 | decision_tag:defer | owner:@leo | next_action:surface warning chips for recency in Pilotage after Wave15 lock. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- Deep RnD D1
  - D1 | recommendation: adaptive recency threshold by activity intensity (idle vs active windows) with deterministic guardrails. | owner:@victor | next_action:prototype threshold policy in tests before runtime adoption. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py | decision_tag:adopt

## Wave16 retention visibility advisory
- Trigger
  - event-driven checkpoint opened on material delta: new Wave16 run artifacts on 2026-02-24.
- Brief 60s
  - On est ou: phase is Ship; codex-only guard is active; new Wave16 runtime checkpoint and dispatch artifacts are published.
  - On va ou: keep dual-root cadence and credit guard until Feb 26, then reopen lanes only if gates stay green.
  - Pourquoi: retention visibility is still warn and overdue, so stale signals can degrade operator trust.
  - Comment: publish only on material delta with evidence-first rows (owner, next_action, evidence_path, decision_tag).
- Recommendations (3 operator rows)
  - R1 | recommendation: restore retention freshness before next operator decision window. | owner:@victor | next_action: regenerate retention_status and confirm next_compaction_at is in the future. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json | decision_tag:adopt
  - R2 | recommendation: keep dual-root recency cadence under credit guard. | owner:@victor | next_action: execute pulse/check loop every 30-45 min and append proof in Wave16 runtime checkpoint logs. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_RUNTIME_CHECKPOINT_2026-02-24T1031Z.md | decision_tag:adopt
  - R3 | recommendation: keep operator trust wording explicit for codex-only isolation. | owner:@clems | next_action: keep codex-only and AG pause wording in operator updates until credits are restored. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md | decision_tag:adopt
- Retention visibility (owner/action/evidence/decision)
  - status: warn
  - policy_version: wave14-7-30-90-permanent-v1
  - generated_at: 2026-02-23T10:27:53+00:00
  - next_compaction_at: 2026-02-23T12:27:53+00:00
  - totals: hot_7d=81 warm_30d=109 cool_90d=0 archive_permanent=0
  - owner: @victor
  - next_action: run manual retention refresh now, then republish status with evidence.
  - evidence_path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
  - decision_tag: defer
- Deep RnD D1 (phase-mapped)
  - D1 | recommendation: retention confidence scorecard from freshness lag + totals stability + checkpoint latency. | owner:@nova | next_action: validate scorecard against three Wave16 artifacts (`runtime checkpoint`, `dispatch guard`, `push receipt`) and record false-alert rate. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_RUNTIME_CHECKPOINT_2026-02-24T1031Z.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE16_DISPATCH_CREDIT_GUARD_2026-02-24.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_PUSH_RECEIPT_2026-02-24.md | decision_tag:defer
- Now/Next/Blockers
  - Now: Wave16 checkpoint refreshed on material delta with 3 operator recommendations + 1 deep D1.
  - Next: publish next checkpoint only when retention/run/blocker/phase delta appears.
  - Blockers: none.
- Blocker escalation rule
  - if blocker age >60 min: post Option A + Option B + Recommended + ping @clems.

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0042-wave10-vulgarisation-clean-simple-tech.md`
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE11_OPERATOR_TRUST_ADVISORY_2026-02-23.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_CP0050_MEMORY_RETENTION_2026-02-23.md`
