# ISSUE-CP-0048 - Wave14 Startup Pack Existing Repo Onboarding

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
Deliver a deterministic startup pack for onboarding an existing repository into Cockpit.

## Scope (In)
- `app/services/brain_manager.py`
- `app/services/project_intake.py`
- `app/data/store.py`
- `app/ui/main_window.py`
- `control/projects/cockpit/docs/` (if needed)

## Done (Definition)
- [x] Existing repo can be attached and initialized without manual file surgery.
- [x] Startup pack includes objective, scope, initial risks, issue seeds, and dispatch hints.
- [x] No cross-project memory contamination.
- [x] Operator can run onboarding with one clear command path.

## Constraints
- existing repos first
- no tournament activation

## Closeout
- Closed at: 2026-02-23T10:26Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE14_VICTOR_LANE_LOCK_2026-02-23T1026Z.md`
- Command path:
  - `/Users/oliviercloutier/Desktop/Cockpit/scripts/project_intake.py`
