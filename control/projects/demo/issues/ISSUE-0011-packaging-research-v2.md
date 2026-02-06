# ISSUE-0011 - Packaging research (macOS .app) (V2)

- Owner: victor
- Phase: Plan
- Status: Todo

## Objective
- Research and prototype packaging Cockpit as a macOS .app (double-click run), without breaking local-first behavior.

## Scope (In)
- Pick a packaging tool (PyInstaller, Briefcase, etc.) and document why.
- Prototype a build that runs on the same machine without venv.
- Confirm file paths / data dir behavior.
- Document the build command + troubleshooting.

## Scope (Out)
- Code signing / notarization.
- Windows/Linux builds.
- Auto-update system.

## Now
- Research options + constraints (PySide6 bundling, size, paths).

## Next
- Prototype build + run on a clean user account (best effort).

## Blockers
- None.

## Done (Definition)
- A documented prototype exists (build command + run steps).
- App launches and can open the demo project.
- Version stamp is still visible (branch@sha may degrade, but version must exist).

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Packaging churn and time sink.
- Runtime path bugs (resources vs working dir).

