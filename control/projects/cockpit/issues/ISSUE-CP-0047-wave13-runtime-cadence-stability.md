# ISSUE-CP-0047 - Wave13 Runtime Cadence Stability

- Owner: victor
- Phase: Implement
- Status: Open

## Objective
Reduce false degraded signals from inactivity by making pulse recency explicit.

## Scope (In)
- `app/services/auto_mode.py`
- `scripts/auto_mode_healthcheck.py`
- `control/projects/cockpit/settings.json`
- `app/ui/project_pilotage.py`

## Done (Definition)
- [ ] Runtime state stores pulse recency (`last_pulse_at`).
- [ ] Healthcheck reports pulse fields and pulse stale issue.
- [ ] Pilotage displays pulse status clearly.
- [ ] No tournament auto-dispatch side effects.

## Notes
- Keep behavior backward compatible.
