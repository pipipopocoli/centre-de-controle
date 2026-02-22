# Assumptions Table

| assumption_id | assumption | why needed now | validation plan | owner_role | decision_date |
|---|---|---|---|---|---|
| ASSUMPTION-A1 | Average operator handles 6-10 active projects per day. | Drives dashboard density and card limits. | Sample 2 weeks of operator sessions and adjust layout. | product_lead | 2026-02-18 |
| ASSUMPTION-A2 | 60-second comprehension target can be achieved with one-screen summary plus progressive disclosure. | Core Variant F goal. | Run timed study on at least 20 sessions in eval harness. | ux_research | 2026-02-18 |
| ASSUMPTION-A3 | Project snapshot generation every 5 minutes is enough for tactical decisions. | Sets cadence and cost baseline. | Compare stale decision rate at 1m, 5m, 15m cadences. | sre | 2026-02-18 |
| ASSUMPTION-A4 | SQLite FTS5 is enough for V2 memory query latency at current scale. | Avoids premature infra complexity. | Load test with 10x data and p95 query thresholds. | backend_lead | 2026-02-18 |
| ASSUMPTION-A5 | Optional semantic index can remain disabled by default without harming operator outcomes. | Keeps V2 simple and low cost. | A/B test retrieval quality with and without semantic layer. | ml_lead | 2026-02-18 |
| ASSUMPTION-A6 | Token spend for narrative summarization stays under baseline budget with compression prompts. | Needed for budget envelope. | Track tokens per update for 30 days and compare to target. | finops | 2026-02-18 |
| ASSUMPTION-A7 | 40-dev parallel delivery can be coordinated with 8 workstreams and weekly integration trains. | Roadmap execution model. | Track dependency wait time and replan after sprint 1. | program_manager | 2026-02-18 |
| ASSUMPTION-A8 | Existing project artifacts are reliable enough to build update snapshots without manual cleanup. | Input readiness for V2 rollout. | Run data quality scan on all active projects. | data_engineer | 2026-02-18 |
| ASSUMPTION-A9 | Visual encoding choices (position/length first) improve decision speed under pressure. | Chart hierarchy decisions. | Usability test with misread-rate metric by chart type. | ux_research | 2026-02-18 |
| ASSUMPTION-A10 | Workers can remain ephemeral without harming traceability if journal and run bundles are complete. | Souls model Option A enforcement. | Audit 50 worker tasks for replay completeness. | reliability_lead | 2026-02-18 |
| ASSUMPTION-A11 | No cross-project retrieval is required for day-to-day operator triage. | Isolation hard constraint. | Monitor cases requesting cross-project context and evaluate frequency. | clems | 2026-02-18 |
| ASSUMPTION-A12 | Desktop offline rendering covers the main operational usage. | Justifies offline-first tab architecture. | Collect runtime environment telemetry and browser capability stats. | frontend_lead | 2026-02-18 |
