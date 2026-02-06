# ISSUE-0001 - Docs/Runbook + Screenshot

- Owner: victor (@victor)
- Phase: Ship
- Status: Done

## Objective
- Clarify how to run Cockpit UI + MCP server with a clean, reproducible quickstart.

## Scope (In)
- Update docs: QUICKSTART.md, GUIDE_INSTALLATION.md, docs/RUNBOOK.md.
- Add/verify UI screenshot in docs.
- Align wording: project targets Python >=3.11; mcp requires >=3.10.

## Scope (Out)
- No functional code changes (keep this PR low risk).

## Now
- Merged to main (2026-02-06).

## Next
- None.

## Blockers
- None

## Done (Definition)
- A new dev can follow QUICKSTART.md and:
- Create venv
- Install deps
- Run python3 tests/verify_mcp_basic.py
- Launch UI (python3 app/main.py)
- Screenshot renders in markdown viewer.
- Changes are reversible (doc-only).

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR: Merged: codex/docs-runbook -> main (2026-02-06)

## Risks
- Docs drift vs actual commands (keep commands minimal and tested).
