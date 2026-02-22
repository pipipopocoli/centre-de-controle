# ISSUE-CP-0029 - Wave05 dispatch backpressure

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Enforce dynamic dispatch cap using queue signal and hard cap guardrail.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json

## Scope (Out)
- Provider execution internals
- Tournament files

## Done (Definition)
- Backpressure cap derived from runtime queue state.
- Hard cap always respected.
- No crash when backpressure config missing.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_auto_mode.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE05.md
