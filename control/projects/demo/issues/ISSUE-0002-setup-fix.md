# ISSUE-0002 - Setup Fix (Repro + Hygiene)

- Owner: victor (@victor)
- Phase: Ship
- Status: Done

## Objective
- Make setup reproducible and keep repo clean (no generated artifacts in git status).

## Scope (In)
- Standardize venv directory name: venv/
- Update .gitignore to ignore venv/ and build artifacts (ex: *.app/).
- Optionally provide a small launcher script (bash) that uses venv/.

## Scope (Out)
- No MCP schema changes (those are ISSUE-0003).

## Now
- Merged to main (2026-02-06).

## Next
- None.

## Blockers
- None

## Done (Definition)
- After setup + run, git status is clean (or only shows intentional edits).
- Setup works with Python 3.11/3.12.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR: Merged: codex/setup-fix -> main (2026-02-06)

## Risks
- Setup instructions differ across machines (keep docs explicit).
