# ISSUE-CP-0049 - Wave14 Mission Critical Commit Gate

- Owner: victor
- Phase: Plan
- Status: Open

## Objective
Enforce mission-critical gate so no commit lands without required evidence and approval.

## Scope (In)
- `app/services/auto_mode.py`
- `scripts/auto_mode.py`
- `app/services/gatekeeper.py`
- `control/projects/cockpit/settings.json`

## Done (Definition)
- [ ] Commit gate requires explicit approval marker for critical lane.
- [ ] Required evidence checklist enforced: tests + screenshots + logs + docs update.
- [ ] Blocker state prevents progression when critical gate is red.
- [ ] Structured error/report when gate fails.

## Constraints
- no hidden bypass
- keep backward compatibility for non-critical lane
