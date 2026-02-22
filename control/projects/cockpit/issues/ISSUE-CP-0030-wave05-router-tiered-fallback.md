# ISSUE-CP-0030 - Wave05 router tiered fallback

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Add provider chain fallback `codex -> antigravity -> ollama` under feature flag.

## Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/ollama_runner.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json

## Scope (Out)
- UI redesign
- Tournament files

## Done (Definition)
- Router attempts providers in configured order.
- Ollama disabled by default and non-fatal if unavailable.
- Existing policy gates remain enforced.

## Test/QA
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_execution_router.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE05.md
