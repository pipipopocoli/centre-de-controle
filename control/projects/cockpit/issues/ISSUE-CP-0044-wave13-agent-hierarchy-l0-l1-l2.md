# ISSUE-CP-0044 - Wave13 Agent Hierarchy L0/L1/L2

- Owner: leo
- Phase: Implement
- Status: Done

## Objective
Render explicit L0/L1/L2 hierarchy in Overview and Pilotage with clear action/waiting/blocked counts.

## Scope (In)
- `app/ui/agents_grid.py`
- `app/ui/project_pilotage.py`
- `app/ui/theme.qss`

## Done (Definition)
- [x] Overview shows sections: L0, L1, L2.
- [x] Each section displays action/attente/bloque/repos counts.
- [x] Pilotage summary includes L0/L1/L2 status rollup.
- [x] Context click behavior remains functional.

## Closeout
- Closed at: 2026-02-23T07:29Z
- Proof pack:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0044_CP0045_PROOF_2026-02-23T0729Z.md`
- Validation highlights:
  - headers: `L0 - Orchestration`, `L1 - Leads`, `L2 - Specialists`
  - per-level summary includes `action | attente | bloque | repos`
  - context click emits payload (`kind=agent`, `id=...`)
  - pilotage health line includes `L0/L1/L2` rollups in simple and tech modes
- Test/QA:
  - `QT_QPA_PLATFORM=offscreen` live widget check (proof pack)

## Notes
- No tournament changes.
