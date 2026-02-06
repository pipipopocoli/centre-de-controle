# ISSUE-0001 - Docs/Runbook + Screenshot

- Owner: victor
- Phase: Review
- Status: In progress

## Objective
- Clarify how to run Cockpit UI + MCP server with a clean, reproducible quickstart.

## Scope (In)
- Update docs: QUICKSTART.md, GUIDE_INSTALLATION.md, docs/RUNBOOK.md.
- Add/verify UI screenshot in docs.
- Align wording: project targets Python >=3.11; mcp requires >=3.10.

## Scope (Out)
- No functional code changes (keep this PR low risk).

## Now
- Runbook exists + screenshot committed, but docs need alignment (venv naming, pip usage, python requirement wording).

## Next
- Fix docs commands to standardize on venv/ + python -m pip.
- Fix screenshot link path in docs/RUNBOOK.md.
- Review control/README.md examples for phase vocabulary.

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
- PR: codex/docs-runbook

## Risks
- Docs drift vs actual commands (keep commands minimal and tested).

