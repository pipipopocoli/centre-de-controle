# Assumptions Table - competitor-r1-e

| assumption_id | statement | why needed | risk_if_wrong | validation_plan | owner_role | due_milestone |
|---|---|---|---|---|---|---|
| A1 | Gate runtime target (p50 25m / p95 45m) is achievable with planned sharding. | Needed to keep developer flow acceptable. | Merge queue stalls and bypass pressure. | Run 2-week load test with realistic commit volume and adjust shard policy. | infra-lead | PI-1 end |
| A2 | Team allocation of ~40 devs is available across 7 workstreams. | Roadmap staffing and parallelism depend on it. | Roadmap slips or scope must shrink. | Confirm with operator capacity plan and re-baseline tickets. | program-lead | PI-0 start |
| A3 | At least 30 representative incident scenarios can be curated for B2 within first 6 weeks. | Needed for strong FN control. | Critical regressions may escape despite green gates. | Build incident ingestion pipeline and weekly curation KPI. | qa-lead | PI-2 mid |
| A4 | Monthly API/token envelope (USD 9k-16k) remains viable under chosen model mix. | Budget policy and guardrails assume this range. | Cost overrun or quality reduction via excessive throttling. | Weekly variance report + optional model-mix fallback plan. | cost-lead | monthly |
| A5 | Hermetic runner images can be pinned across all relevant environments. | Deterministic replay depends on stable runtime. | Nondeterminism triggers false blocks. | Reproducibility test matrix across runner pools. | runtime-lead | PI-1 end |
| A6 | Approval and audit workflow overhead stays below 8 percent cycle-time tax. | Governance should not paralyze delivery. | Team bypasses process and weakens controls. | Measure cycle-time delta before/after enforcement and tune policy tiers. | policy-lead | PI-2 end |
