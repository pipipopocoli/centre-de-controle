# WAVE09 Precheck - 2026-02-20

## Objective
- Capture kickoff truth before Wave09 dispatch.
- Confirm dual-root status and identify immediate blockers.

## Commands executed
1. Repo pulse
- `./.venv/bin/python scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify`
2. AppSupport pulse
- `./.venv/bin/python scripts/auto_mode.py --project cockpit --once --max-actions 0 --no-open --no-clipboard --no-notify`
3. Repo healthcheck
- `./.venv/bin/python scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --data-dir repo`
4. AppSupport healthcheck
- `./.venv/bin/python scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3`

## Results snapshot

### Repo root (`control/projects`)
- status: healthy
- open_requests_external: 1
- tick_age_seconds: 9
- issues: none

### AppSupport root (`~/Library/Application Support/Cockpit/projects`)
- status: degraded
- open_requests_external: 0
- tick_age_seconds: 5
- snapshot_age_seconds: 6562
- issues:
  - `stale_kpi_snapshot`

## Interpretation
- Queue control is currently clean on both roots.
- Remaining risk is recency contract drift on AppSupport KPI snapshot.
- Wave09 P0 must close this before deeper implementation lanes.

## Next actions
1. Launch CP-0035 (dual-root cadence and reconciliation runbook).
2. Launch CP-0036 (healthcheck deterministic hardening).
3. Keep 30-45 minute operator cadence checks until both roots remain healthy across two checkpoints.
