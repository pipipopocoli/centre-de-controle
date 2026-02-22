# ISSUE-CP-0001 - Skills catalog fetch cache fallback

- Owner: victor -> @agent-2
- Phase: Ship
- Status: Done

## Objective
- Build reliable catalog fetch with local cache and network fallback behavior.

## Scope (In)
- Add catalog fetch service.
- Add local cache read/write.
- Add fail-open fallback when remote fetch fails.

## Scope (Out)
- UI rendering of catalog.
- Skill install execution logic.

## Now
- Done.

## Next
- None.

## Blockers
- None.

## Done (Definition)
- [x] Fetch returns deterministic catalog payload.
- [x] Cache used when network fails.
- [x] Test proof available (9/9 pass).

## Proof
- Module: `app/services/skills_catalog.py`
- Tests: `tests/verify_skills_catalog.py` (9 passed, 0 failed)

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md

## Risks
- Cache staleness and partial payload writes (mitigated by atomic writes).

