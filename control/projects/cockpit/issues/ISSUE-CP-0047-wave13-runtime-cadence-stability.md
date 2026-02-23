# ISSUE-CP-0047 - Wave13 Runtime Cadence Stability

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
Reduce false degraded signals from inactivity by making pulse recency explicit.

## Scope (In)
- `app/services/auto_mode.py`
- `scripts/auto_mode_healthcheck.py`
- `control/projects/cockpit/settings.json`
- `app/ui/project_pilotage.py`

## Done (Definition)
- [x] Runtime state stores pulse recency (`last_pulse_at`).
- [x] Healthcheck reports pulse fields and pulse stale issue.
- [x] Pilotage displays pulse status clearly.
- [x] No tournament auto-dispatch side effects.

## Closeout
- Closed at: 2026-02-23T07:24Z
- Proof pack:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0046_CP0047_PROOF_2026-02-23T0724Z.md`
- Checkpoint evidence:
  - healthy: `status=healthy`, `issues=[]` (`--stale-seconds 120`, app root)
  - stale: `status=degraded`, `issues=[stale_tick,pulse_stale]` (`--stale-seconds 1`, app root)
  - recovered after pulse: `status=healthy`, `issues=[]` (`--stale-seconds 1` after `scripts/auto_mode.py --once`)
- Test/QA:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`

## Now / Next / Blockers
- Now: CP-0046/CP-0047 closed with live evidence and pulse checkpoint proof.
- Next: keep 2h cadence reports and monitor pulse recency drift.
- Blockers: none.

## Notes
- Keep behavior backward compatible.
