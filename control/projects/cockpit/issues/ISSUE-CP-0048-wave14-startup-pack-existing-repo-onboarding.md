# ISSUE-CP-0048 - Wave14 Startup Pack Existing Repo Onboarding

- Owner: victor
- Phase: Plan
- Status: Open

## Objective
Deliver a deterministic startup pack for onboarding an existing repository into Cockpit.

## Scope (In)
- `app/services/brain_manager.py`
- `app/services/project_intake.py`
- `app/data/store.py`
- `app/ui/main_window.py`
- `control/projects/cockpit/docs/` (if needed)

## Done (Definition)
- [ ] Existing repo can be attached and initialized without manual file surgery.
- [ ] Startup pack includes objective, scope, initial risks, issue seeds, and dispatch hints.
- [ ] No cross-project memory contamination.
- [ ] Operator can run onboarding with one clear command path.

## Constraints
- existing repos first
- no tournament activation
