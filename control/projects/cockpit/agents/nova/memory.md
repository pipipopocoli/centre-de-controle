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

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0042-wave10-vulgarisation-clean-simple-tech.md`
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`
