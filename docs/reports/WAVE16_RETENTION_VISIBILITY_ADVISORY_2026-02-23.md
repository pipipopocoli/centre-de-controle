# Wave16 Retention Visibility Advisory (2026-02-23)

## Objective
Run Nova Wave16 advisory lane with retention-first visibility in vulgarisation, a <=60s operator digest, and one deep RnD item mapped to phase.

## Brief 60s
- On est ou: retention signal is now rendered in vulgarisation header, Brief 60s, Simple what-next, and Tech retention section.
- On va ou: keep manual 2h checkpoints and refresh retention_status before next operator decision window.
- Pourquoi: if retention freshness is stale, operator trust drops and decisions degrade.
- Comment: keep owner/action/evidence/decision_tag explicit and republish Now/Next/Blockers every checkpoint.

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
- hint: retention checkpoint is overdue; run immediate refresh.

## Deep RnD D1 (phase-mapped)
- D1 | recommendation: retention confidence rubric combining status/freshness/totals/action clarity into one operator score.
- owner: @nova
- next_action: validate the rubric on 3 consecutive refresh cycles and compare decision latency before/after.
- evidence_path:
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
- decision_tag: defer

## Now/Next/Blockers
- Now: Wave16 retention visibility is active in service output and advisory artifacts.
- Next: execute manual retention refresh, then publish next 2h checkpoint with updated status and compaction time.
- Blockers: none.

## Cadence 2h
- Manual loop only (no automation in this delivery): chat + memory + this rolling report.
- Wording/readability pass: @agent-11.

## Evidence paths
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/retention/retention_status.json
