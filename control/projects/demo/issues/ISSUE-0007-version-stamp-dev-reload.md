# ISSUE-0007 - Version stamp + dev reload

- Owner: victor
- Phase: Implement
- Status: In progress

## Objective
- Show a visible version stamp (branch + short SHA + dirty flag) and the data dir path.
- Add dev reload for QSS theme to speed UI iteration.

## Scope (In)
- Version stamp always visible (window title and/or sidebar footer).
- Show data dir path (control/projects/...) for debugging.
- Load QSS from file and hot-reload on save via QFileSystemWatcher.
- Update docs/RUNBOOK.md with launch command and version check.

## Scope (Out)
- Production build packaging changes.
- Automated release versioning.

## Spec (Minimal)
- Version stamp = "<branch>@<sha><*dirty>"
- Example: "main@3649287*"
- Data dir = path to control/projects

## Done (Definition)
- Version stamp visible at all times.
- Data dir visible in UI.
- QSS reloads on file save.
- RUNBOOK updated with launch command and version check.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:
