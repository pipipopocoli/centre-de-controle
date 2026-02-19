# CP-0031 Cost Telemetry Note - 2026-02-19

## Scope
- Issue: ISSUE-CP-0031 (Wave05 cost telemetry CAD)
- Goal: lock one shared CAD cost telemetry schema and one reproducible monthly estimator.
- Policy: `runs/cost_events.ndjson` is runtime generated and is not committed as sample data.

## Canonical schema
- Schema version: `wave05_cost_event_v2`
- Canonical file: `control/projects/<project_id>/runs/cost_events.ndjson`

### Required fields
| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | must equal `wave05_cost_event_v2` |
| `run_id` | string | non-empty |
| `project_id` | string | non-empty |
| `agent_id` | string | non-empty |
| `provider` | string | non-empty |
| `input_tokens` | int | `>= 0` |
| `output_tokens` | int | `>= 0` |
| `cached_tokens` | int | `>= 0` |
| `cached_input_tokens` | int | `>= 0`, must match `cached_tokens` |
| `elapsed_ms` | int | `>= 0` |
| `currency` | string | must be `CAD` |
| `cost_cad_estimate` | number | `>= 0` |
| `timestamp` | ISO string | parseable UTC timestamp |
| `ts` | number | epoch seconds |

## Monthly estimator contract
- Authoritative source order:
1. Current UTC month events from `runs/cost_events.ndjson`
2. Legacy fallback `vulgarisation/costs.json` only if valid event count is zero

- UTC month filter:
  - month key: `now_utc.strftime("%Y-%m")`
  - event datetime resolution:
1. use `ts` first
2. fallback to `timestamp`

- Formula:
  - `monthly_cad = sum(cost_cad_estimate for valid events in current UTC month)`
  - `event_count = number of valid events in current UTC month`

## Repro commands
Run from repo root:

```bash
cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_wave05_router_fallback.py
cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_execution_router.py
cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_bible.py
cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_cost_telemetry.py
```

Expected success lines:
- `OK: wave05 router fallback + cost + slo artifacts verified`
- `OK: execution router verified`
- `OK: monthly estimator source order verified`
- `OK: cost telemetry schema + monthly estimator verified`

## Notes
- Emission validation is non-fatal: invalid events are dropped and logged as `cost_event_dropped`.
- The same estimator module is used by:
  - router schema validation path
  - vulgarisation snapshot cost panel
  - pilotage health line cost readout
