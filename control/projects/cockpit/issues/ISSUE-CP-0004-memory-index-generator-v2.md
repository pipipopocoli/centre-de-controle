# ISSUE-CP-0004 - Memory index generator v2

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Generate deterministic `memory.index.json` from project memory/chat/journal signals.

## Scope (In)
- Index generator for clems/victor/leo.
- Deterministic ordering.
- Stable section layout.

## Scope (Out)
- Semantic retrieval.
- Memory rewrite automation.

## Now
- Deterministic generator implemented in `app/services/memory_index.py`.
- CLI flow updated in `scripts/memory_index.py`.

## Next
- Monitor output size and keep section caps stable.
- Keep schema additive-only for backward compatibility.

## Blockers
- None.

## Done (Definition)
- Index file generated for all three core roles.
- Re-running generator yields same output for same input.
- Tests pass.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- Service: /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- Script: /Users/oliviercloutier/Desktop/Cockpit/scripts/memory_index.py
- Test: /Users/oliviercloutier/Desktop/Cockpit/tests/verify_memory_index.py
- PR: main (V2-WAVE-03)

## Risks
- Non-deterministic ordering from mixed timestamps.

## Proof
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_index.py`
- Result: deterministic index checks pass (two consecutive runs produce identical payloads).
