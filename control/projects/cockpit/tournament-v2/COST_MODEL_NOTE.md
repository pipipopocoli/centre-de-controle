# COST MODEL NOTE - Subscription vs API pay-per-token

## 0) Purpose
- Normalize cost comparisons across subscription tools and API usage.
- Support go/no-go decisions with quantified scenarios.

## 1) Currency and scope
- Currency: CAD for reporting.
- Internal compute and human time can be added as separate columns.
- API estimates are model-specific and scenario-dependent.

## 2) Base formula
Let:
- input_tokens
- output_tokens
- cached_input_tokens
- price_in_per_million
- price_out_per_million
- price_cached_in_per_million
- runs_per_month
- agents_per_run

Single run API cost:
`api_cost = (input_tokens/1_000_000)*price_in_per_million + (output_tokens/1_000_000)*price_out_per_million + (cached_input_tokens/1_000_000)*price_cached_in_per_million`

Monthly API cost estimate:
`monthly_api = api_cost * runs_per_month * agents_per_run`

CAD conversion:
`monthly_api_cad = monthly_api_usd * usd_to_cad_rate`

## 3) Scenario set (mandatory)
Define at least four scenarios:
- small
- medium
- large
- xlarge

Each scenario must specify:
- avg input tokens per agent-run
- avg output tokens per agent-run
- avg cached input tokens
- runs/month
- agents/run
- model mix

## 4) Break-even method
Compare three strategies:
- subscription-only
- hybrid (subscription + API bursts)
- API-first

Break-even steps:
1. Estimate monthly subscription baseline in CAD.
2. Estimate monthly API cost in CAD by scenario.
3. Add operational overhead estimate.
4. Find usage point where API or hybrid becomes cheaper or more predictable.

## 5) Sensitivity analysis
Run parameter sweeps for:
- runs/month
- agents/run
- output/input ratio
- cache hit ratio
- usd_to_cad rate

Report:
- base case
- optimistic
- conservative

## 6) Logging schema (minimum)
Log one record per agent-run event:
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

Recommended path:
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/runs/cost_events.ndjson`

## 7) Weekly and monthly reporting
Weekly report fields:
- total runs
- total tokens in/out/cached
- total estimated API CAD
- avg CAD per run
- top expensive workflows

Monthly report fields:
- strategy comparison table
- budget vs actual
- trend vs prior month
- optimization opportunities

## 8) Decision matrix
Use these outcomes:
- keep subscription:
  - stable interactive use
  - low variance workloads
- hybrid:
  - mixed interactive + batch workloads
  - occasional heavy evaluation bursts
- api-first:
  - high-volume automated workloads
  - clear metering and strict budget controls

## 9) Governance and approvals
- Any new billable API pattern outside agreed baseline requires @clems approval.
- Cost model updates require dated changelog entry.
- Assumptions must be explicit and versioned.

## 10) Minimum acceptance criteria
- Four scenarios filled with numbers.
- CAD conversion shown.
- break-even comparison included.
- sensitivity section included.
- logging schema adopted in project docs.
