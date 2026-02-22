# ISSUE-CP-0033 - Wave06 Nova global L1

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Establish Nova as the global L1 agent for creative/scientific reasoning tasks.
- Lock timeline feed ordering to be deterministic.

## Scope (In)
- `agents/nova/*`
- `app/data/store.py`
- `app/services/chat_parser.py`
- `app/services/memory_index.py`
- `app/services/timeline_feed.py`
- `tests/verify_wave06_nova.py`
- `tests/verify_timeline_feed.py`

## Scope (Out)
- Tournament activation
- Cross-project retrieval changes

## Done (Definition)
- Nova files exist for active project under `control/projects/cockpit/agents/nova/`.
- `@nova` mention parsing works in runtime flow.
- Timeline feed order is stable across re-runs.
- Verification suite passes.

## Test/QA
- `./.venv/bin/python tests/verify_wave06_nova.py`
- `./.venv/bin/python tests/verify_timeline_feed.py`
- `./.venv/bin/python tests/verify_memory_index.py`

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE06_CLOSEOUT_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE06_BACKEND_SHIP_READINESS_2026-02-19T1728Z.md
