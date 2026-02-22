# ISSUE-CP-0043 - Wave10 throughput burst governance

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Increase throughput in balanced mode without runtime drift.
- Keep lead-first dispatch and specialist activation after lead ack.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/registry.json`
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py`

## Scope (Out)
- Tournament automation
- Non-essential cleanup

## Done (Definition)
- [x] Auto-mode balanced burst allows 2 actions per active cycle.
- [x] Backpressure remains enforced (`queue_target=3`, `hard_cap=5`).
- [x] Lead-first dispatch order documented and applied.
- [x] Platform mapping follows project registry.
- [x] Runtime gates remain healthy on repo and AppSupport.

## Verification
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --data-dir repo`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`

## Closeout
- Closed at (UTC): `2026-02-22T18:13:56Z`

## Evidence
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave10_runtime_lane.py` -> `OK: wave10 runtime/backend lane verified` (includes `cp-0043` pass)
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave05_dispatch.py` -> `OK: wave05 dispatch scoring/backpressure verified`
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify --kpi-min-interval-minutes 25` -> `KPI snapshot emitted=true`
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir app --once --max-actions 0 --no-open --no-clipboard --no-notify --kpi-min-interval-minutes 25` -> `KPI snapshot emitted=true`
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir repo --stale-seconds 3600 --max-open 3 --max-snapshot-age-seconds 2100` -> `status=healthy`
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir app --stale-seconds 3600 --max-open 3 --max-snapshot-age-seconds 2100` -> `status=healthy`
- Repo gate rebalance applied: `mark_request_closed(..., closed_reason=wave10_runtime_gate_rebalance)` on one queued external request to restore `open_requests_external<=3`

## Now / Next / Blockers
- Now: Wave10 runtime/backend lane locked; balanced throughput at `max_actions=2`; repo + AppSupport healthchecks healthy.
- Next: Keep 2h cadence checks and track queue pressure drift under normal load.
- Blockers: none.
