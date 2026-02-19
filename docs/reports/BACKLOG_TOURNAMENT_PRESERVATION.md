# BACKLOG TOURNAMENT PRESERVATION

## Status
- Mode: dormant
- Scope: preserved for operator activation only
- Last update: 2026-02-19

## Reusable entrypoints
- Tournament V1 root:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
- Tournament V2 root:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`
- Arena UI:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/TOURNAMENT_ARENA.html`
  - `/Users/oliviercloutier/Desktop/Cockpit/site/`
- Dispatch/report examples:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/start_mission.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/report_debug_to_clems.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/report_ui_qa.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/reply_to_inbox.py`

## Required inputs
- Active project lock:
  - `PROJECT LOCK: cockpit`
- Round policy:
  - target round id (`R1`, `R2`, `L3`, `L4`)
- Competitor roster:
  - agent ids and platform map (`Codex` or `Antigravity`)
- Prompt contract:
  - final output paths and mandatory sections
- Judging contract:
  - rubric, tie-break, veto rules

## Required outputs
- Round dispatch pack:
  - prompt files and per-agent readme files
- Submission index:
  - who submitted, missing files, readiness by fight
- Judge feedback:
  - winner, rationale, imports required
- Operator summary:
  - one page status and next dispatch actions

## Activation checklist
1. Confirm app runtime is stable for implementation lane (no hard blocker).
2. Confirm tournament trees are intact under `control/projects/cockpit/`.
3. Confirm round scope and roster are explicit.
4. Confirm prompt templates match current policy (final-only, dual-stage, etc).
5. Confirm scoreboard secrecy policy for agents.
6. Confirm dispatch lines are copy/paste ready.
7. Confirm submission paths exist before launch.
8. Confirm judge templates exist before first submission.
9. Launch dispatch manually.
10. Run post-round lock and archive notes.

## Risks
- Drift risk:
  - tournament prompt contracts diverge from current app/runtime policies.
- Noise risk:
  - archived rounds create confusion with active round artifacts.
- Scope collision risk:
  - tournament work starts blocking implementation throughput.
- Data integrity risk:
  - manual dispatch without strict path lock creates wrong-project writes.
- Ops risk:
  - score details accidentally exposed to competitors.

## Guardrails
- Tournament is operator-triggered only.
- No auto-dispatch.
- No deletion of tournament trees during cleanup.
- Keep implementation lane priority over tournament lane.
- Keep strict project lock in every prompt packet.
- Keep score details internal, publish verdict only.
- Archive each completed round with an explicit status file.

## Owner and next review
- Owner: @clems
- Next review gate: when V2 implementation reaches next stable checkpoint.
