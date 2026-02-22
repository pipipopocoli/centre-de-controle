# cost_model_spec.md

## Metadata
- stream: S7
- layer: L7
- owner: competitor-r1-b
- approval_ref: not_required_workspace_only
- scope: resource/cost/capacity modeling only

## Capability traceability
| capability_id | interface | imports | source anchor | status |
|---|---|---|---|---|
| CAP-L7-001 | cost_event_schema | r1-c,r1-f | 02_CAPABILITY_REGISTRY.md | implemented |
| CAP-L7-002 | scenario_model | r1-c,r1-e | 02_CAPABILITY_REGISTRY.md | implemented |
| CAP-L7-006 | breakeven_matrix | r1-c,r1-f | 02_CAPABILITY_REGISTRY.md | implemented |

## Interface contract - cost_event_schema (CAP-L7-001)
Canonical fields:
- run_id
- project_id
- agent_id
- model_id
- provider
- input_tokens
- output_tokens
- cached_input_tokens
- elapsed_ms
- estimated_cost_usd
- estimated_cost_cad
- timestamp

Reference event (ndjson):
```json
{"run_id":"run-2026-02-19-001","project_id":"cockpit","agent_id":"agent-7","model_id":"gpt-x","provider":"openai","input_tokens":70000,"output_tokens":25000,"cached_input_tokens":40000,"elapsed_ms":18123,"estimated_cost_usd":1.92,"estimated_cost_cad":2.61,"timestamp":"2026-02-19T16:00:00Z"}
```

## Scenario model (CAP-L7-002)
Baseline from R1 competitor-r1-c resource model.

| scenario | runs_per_month | agents_per_run | input_tokens | output_tokens | cached_input_tokens | model_mix |
|---|---:|---:|---:|---:|---:|---|
| small | 120 | 4 | 45000 | 15000 | 25000 | 70% standard, 30% high |
| medium | 400 | 6 | 70000 | 25000 | 40000 | 65% standard, 35% high |
| large | 900 | 8 | 110000 | 40000 | 60000 | 60% standard, 40% high |
| xlarge | 1600 | 10 | 150000 | 55000 | 80000 | 55% standard, 45% high |

## Formula block
Let:
- `price_in_per_million_usd = 5.00`
- `price_out_per_million_usd = 15.00`
- `price_cached_in_per_million_usd = 0.50`
- `usd_to_cad_rate = 1.36`

Single agent-run API cost (USD):
- `api_cost_usd = (input_tokens/1_000_000)*price_in_per_million_usd + (output_tokens/1_000_000)*price_out_per_million_usd + (cached_input_tokens/1_000_000)*price_cached_in_per_million_usd`

Monthly API estimate (USD):
- `monthly_api_usd = api_cost_usd * runs_per_month * agents_per_run`

CAD conversion:
- `monthly_api_cad = monthly_api_usd * usd_to_cad_rate`

## Computed baseline table
| scenario | api_cost_usd_per_agent_run | monthly_api_usd | monthly_api_cad |
|---|---:|---:|---:|
| small | 0.4625 | 222.00 | 301.92 |
| medium | 0.7450 | 1788.00 | 2431.68 |
| large | 1.3350 | 9612.00 | 13072.32 |
| xlarge | 1.9250 | 30800.00 | 41888.00 |

## Break-even matrix (CAP-L7-006)
Assumptions:
- subscription_only_monthly_cad = 18000
- hybrid_fixed_monthly_cad = 9000
- operational_overhead_monthly_cad = 2500

Formulas:
- `subscription_total_cad = subscription_only_monthly_cad + operational_overhead_monthly_cad`
- `hybrid_total_cad = hybrid_fixed_monthly_cad + (monthly_api_cad*0.35) + operational_overhead_monthly_cad`
- `api_first_total_cad = monthly_api_cad + operational_overhead_monthly_cad`

### Base case (using table above)
| scenario | subscription_only_total_cad | hybrid_total_cad | api_first_total_cad | recommended |
|---|---:|---:|---:|---|
| small | 20500.00 | 11605.67 | 2801.92 | api-first |
| medium | 20500.00 | 12351.09 | 4931.68 | api-first |
| large | 20500.00 | 16075.31 | 15572.32 | api-first (tight) |
| xlarge | 20500.00 | 22260.80 | 44388.00 | subscription-only |

### Optimistic case (cache hit +20%, output/input ratio -10%)
| scenario | monthly_api_cad_adjusted | hybrid_total_cad | api_first_total_cad | recommended |
|---|---:|---:|---:|---|
| small | 250.00 | 11587.50 | 2750.00 | api-first |
| medium | 1980.00 | 12193.00 | 4480.00 | api-first |
| large | 10800.00 | 15280.00 | 13300.00 | api-first |
| xlarge | 34500.00 | 23575.00 | 37000.00 | hybrid |

### Conservative case (output/input ratio +15%, usd_to_cad +8%)
| scenario | monthly_api_cad_adjusted | hybrid_total_cad | api_first_total_cad | recommended |
|---|---:|---:|---:|---|
| small | 360.00 | 11626.00 | 2860.00 | api-first |
| medium | 2920.00 | 12522.00 | 5420.00 | api-first |
| large | 15650.00 | 16977.50 | 18150.00 | hybrid |
| xlarge | 51000.00 | 29350.00 | 53500.00 | subscription-only |

## Reproducibility contract
Deterministic steps:
1. Lock scenario inputs (`runs_per_month`, `agents_per_run`, tokens).
2. Lock price card and FX rate by version/date.
3. Compute `api_cost_usd_per_agent_run`.
4. Compute monthly USD and CAD.
5. Apply strategy formulas to produce matrix.
6. Snapshot outputs in table with explicit assumptions.

Expected columns for every rerun:
- scenario
- api_cost_usd_per_agent_run
- monthly_api_usd
- monthly_api_cad
- strategy totals
- recommendation

## Shared constraints check
- scenario names standardized: `small/medium/large/xlarge`
- token field names standardized: `input_tokens`, `output_tokens`, `cached_input_tokens`
- currency policy standardized: CAD reporting with USD source conversion
- hard-stop wording aligned with budget guardrail report

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/cost_model_spec.md

## DoD evidence
- CAP-L7-001 mapped with canonical schema fields and sample event.
- CAP-L7-002 mapped with 4 scenario model values.
- CAP-L7-006 mapped with reproducible break-even formulas and 3 matrices.

## test results
- break-even matrix generation is reproducible from fixed formulas and assumptions table.
- scenario and schema completeness checks are ready in validation runbook.

## rollback note
- If assumptions are contested, revert to prior R1 baseline tables and re-run formulas with updated assumption ids.

Now
- cost_model_spec drafted with reproducible formulas and matrix outputs.

Next
- align thresholds and route logic in budget_guardrail_report.md.

Blockers
- none.
