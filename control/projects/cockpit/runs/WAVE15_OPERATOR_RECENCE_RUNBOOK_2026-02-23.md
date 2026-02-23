# Wave15 Operator Recency Runbook (repo + AppSupport)

## Objective
Keep runtime recency healthy on both roots and avoid stale-only false degraded signals after a fresh pulse.

## Commands

### Repo pulse
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify
```

### AppSupport pulse
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --once --max-actions 0 --no-open --no-clipboard --no-notify
```

### Repo healthcheck
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --data-dir repo
```

### AppSupport healthcheck
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3
```

## Expected transitions
- degraded -> healthy after pulse when only recency gates were stale.
- `stale_tick` or `pulse_stale` remains blocking (`status=degraded`).
- `stale_kpi_snapshot` is warning-only (`stale_kpi_snapshot_soft`) when `last_pulse_at` is fresh.

## Cadence
- Run pulse + healthcheck every 30-45 minutes during active wave execution.

## Advisory ledger
- owner: @nova
- next_action: run dual-root pulse/check sequence before each gate checkpoint.
- evidence_path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_OPERATOR_RECENCE_RUNBOOK_2026-02-23.md
- decision_tag: adopt
