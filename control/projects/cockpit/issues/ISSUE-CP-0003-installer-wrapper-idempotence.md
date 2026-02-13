# ISSUE-CP-0003 - Installer wrapper idempotence

- Owner: victor -> @agent-3
- Phase: Ship
- Status: Done

## Objective
- Add installer wrapper with idempotent install behavior and dry-run support.

## Scope (In)
- Wrapper command surface.
- Idempotent detection (skip already installed).
- Dry-run output contract.

## Scope (Out)
- UI controls for installer.
- Catalog fetch implementation.

## Now
- Done.

## Next
- None.

## Blockers
- None.

## Done (Definition)
- [x] Repeated install does not re-install unchanged skills.
- [x] Dry-run reports actions without mutation.
- [x] Logs include installed/skipped/failed counters.

## Proof
- Service: `/Users/oliviercloutier/Desktop/Cockpit/app/services/skills_installer.py`
- Wrapper: `/Users/oliviercloutier/Desktop/Cockpit/scripts/skills_install_wrapper.py`
- Tests: `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_skills_installer.py` (6 passed, 0 failed)
- Regression: `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_skills_catalog.py` (9 passed, 0 failed)
- Regression: `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_skills_policy.py` (9 passed, 0 failed)
- Smoke: `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_basic.py` (2 passed, 0 failed, mock MCP mode)

## Validation commands
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_skills_installer.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_skills_catalog.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_skills_policy.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_basic.py`

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- PR: TDB (branch local updated with CP-0003 changes)

## Risks
- False positives in idempotence detection.
