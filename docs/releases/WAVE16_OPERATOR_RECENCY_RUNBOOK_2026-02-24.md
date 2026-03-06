# Wave16 Operator Recency Runbook (Codex-Only Window)

Timestamp (UTC): 2026-02-24T00:00:00Z
Scope: `repo` + `AppSupport` dual-root cadence

## Objective
Keep runtime health green during Wave16 while AG is unavailable.

## Cadence (every 30-45 min)
1. Repo pulse:
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --pulse-only
```
2. AppSupport pulse:
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --pulse-only
```
3. Repo healthcheck:
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir repo --stale-seconds 3600 --max-open 3 --autopulse-guard
```
4. AppSupport healthcheck:
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --autopulse-guard
```

## Expected transitions
- Immediately after pulse+check: `status=healthy`.
- Without cadence for >1h: `stale_tick` / `pulse_stale` can return and degrade status.
- `stale_kpi_snapshot` alone should be warning-only when pulse is fresh.

## Credit guard
- Active policy:
  - `start_credits=594`
  - `wave_cap<=180`
  - `reserve_floor>=350`
  - `max_actions_effective=1`
- Stop rule:
  - if remaining credits <=350, freeze new implementation prompts and run maintenance cadence only.

## Ownership
- Runtime lane owner: `@victor`
- Operator oversight: `@clems`
