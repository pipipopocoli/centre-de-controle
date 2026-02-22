# Wave09 Nova PLAN Kickoff - 2026-02-20T21:38:41Z

## Objective
- Run @nova as dual lane advisory:
  - lane A operator-first vulgarisation,
  - lane B deep scientific RnD scouting.

## Sources used
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_PRECHECK_2026-02-20.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-NOVA-WAVE09-RESEARCH.md

## Scope guard
- No proposal to edit:
  - /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
  - /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py
  - /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss

## Brief 60s
- On est ou: Wave09 is in Implement. Repo root is healthy. AppSupport is degraded only on stale_kpi_snapshot.
- On va ou: close CP-0035 first, then CP-0036, to lock dual-root cadence and deterministic healthcheck behavior.
- Pourquoi: stale KPI recency can create false degraded states and break operator trust in gate signals.
- Comment: keep strict pulse plus healthcheck cadence, publish Now/Next/Blockers every 2h, and route one owner-bound recommendation each checkpoint.

## Research questions (top 3)
1. Q1 - Which KPI recency contract removes false stale_kpi_snapshot without masking real incidents?
- Why now: active P0 blocker in Wave09 state and precheck.
- Expected impact: stable gate trust and fewer false degraded alerts.
- Proof: two consecutive checkpoints with repo plus AppSupport healthy and no stale_kpi_snapshot.
- Confidence: high.
- Risk: stale threshold overfit can hide real regressions.

2. Q2 - Which minimum dual-root wording best improves operator clarity without UI overlap?
- Why now: operator trust drift risk is explicit in current state.
- Expected impact: faster and clearer go or hold decisions.
- Proof: repeated checkpoint notes remain unambiguous and accepted by owners.
- Confidence: medium.
- Risk: message can become noisy if wording is too verbose.

3. Q3 - Which adopt/defer/reject SLA keeps Nova recommendations actionable per checkpoint?
- Why now: ADR-CP-011 requires phase-linked deep RnD outputs and decision ledger discipline.
- Expected impact: less advisory backlog and better owner accountability.
- Proof: 100 percent recommendations with owner ack or explicit pending reason in next cycle.
- Confidence: medium.
- Risk: delayed owner ack can keep high-priority items pending.

## Top recommendation (P0)
- decision_tag: adopt
- owner: @victor
- next action: close ISSUE-CP-0035 with explicit recency reconciliation rules, then validate deterministic behavior in ISSUE-CP-0036.
- evidence path:
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_PRECHECK_2026-02-20.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE09_CP0035_CP0038.md

## Status
- Now: PLAN kickoff packet published for dual-lane Nova.
- Next: continue 2h checkpoint cycle with refreshed brief, 3 research questions, and one top recommendation.
- Blockers: AppSupport stale_kpi_snapshot remains open until CP-0035 reconciliation lands.
