# Paper Plan - V2 Wave04 Parallelization Max

## Objective
- Launch Wave04 now with maximum safe parallelization.
- Keep runtime control gates green while execution moves.
- Keep tournament capability dormant and preserved.

## Baseline (T0)
- Wave03 closeout is complete: CP-0004, CP-0005, CP-0015 are done.
- Runtime gates at T0:
  - pending_stale_gt24h = 0
  - queued_runtime_requests = 0
  - stale_heartbeats_gt1h = 0
- Tournament remains operator-triggered only.

## Parallel chains (owner unique)
| Chain | Owner | Support | Goal | Required output |
|---|---|---|---|---|
| C0 Control loop | @clems | @victor | Keep runtime gates green every 60m | control snapshot + queue recovery log |
| C1 UI ship lock | @leo | @agent-6, @agent-7 | Lock UI render + final evidence | CP-0015 delta pack + captures + matrix |
| C2 Backend contract lock | @victor | @agent-1, @agent-3 | Lock MCP/memory deterministic contract | backend test report + deterministic proof |
| C3 Cleanup decisions | @agent-11 | @clems | Decide canonical spec/env/docs | cleanup decision note + archive policy |
| C4 Wave04 prep | @clems | @victor, @leo | Prepare next sprint dispatch | Wave04 dispatch pack + CP-002x issue map |

## Sequence (6h)
### T+0 to T+15 kickoff
1. Dispatch missions to @victor and @leo.
2. Require ack `Now/Next/Blockers` under 15 minutes.
3. Start C3 and C4 in draft mode.
4. Enforce WIP max = 5.

### T+15 to T+120 execution
1. C0: recheck `requests.ndjson`, `agents/*/state.json`, `chat/global.ndjson` every 60m.
2. C1: finalize `app/ui/agents_grid.py`, `app/ui/theme.qss`, CP0015 docs.
3. C2: run MCP/memory tests and 2-run determinism proof.
4. C3: choose canonical build spec, canonical venv, canonical V2 docs root.
5. C4: prepare Wave04 backlog, owners, dispatch lines, gates.

### T+120 Gate 1 (hard)
- C1 expected:
  - QA matrix complete
  - captures complete
  - no critical UI regression
- C2 expected:
  - backend tests green
  - MCP contract stable
- C0 expected:
  - runtime gates still green
- If any lane is red:
  - reallocate inside same lane
  - no new scope

### T+120 to T+240 integration
1. C1 + C2 close residual gaps.
2. C3 publishes cleanup decision note (no destructive cleanup).
3. C4 converts draft to executable issue + dispatch pack.

### T+240 Gate 2 (ship readiness)
- Preconditions: C0 green, C1 green, C2 green.
- Actions:
  - publish ship-ready packet
  - lock `STATE.md` and `ROADMAP.md` with final references

### T+240 to T+360 launch prep final
1. Freeze Wave04 prompt pack.
2. Assemble dispatch order by lane.
3. Lock checkpoints at T+2h / T+4h / T+6h.
4. Keep tournament dormant (no auto-dispatch).

## Gate checklist
1. Runtime control:
- pending_stale_gt24h == 0
- queued_runtime_requests <= 3 (target 0)
- stale_heartbeats_gt1h <= 2
2. UI:
- CP0015 matrix complete
- degraded-state evidence present
3. Backend:
- MCP tools callable
- memory determinism verified
4. Governance:
- tournament paths untouched
- no automatic tournament dispatch

## Risks and mitigations
- Risk: stale loop returns after reminders.
  - Mitigation: C0 60m cadence + explicit transition logging.
- Risk: false green from old artifacts.
  - Mitigation: Gate 1 and Gate 2 require fresh proofs in this wave.
- Risk: cleanup impacts tournament capability.
  - Mitigation: hard exclusion rules from BACKLOG_TOURNAMENT_PRESERVATION.md.

## References
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE04_GATE_CHECKLIST_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE04_DISPATCH_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_CLEANUP_V2.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md
