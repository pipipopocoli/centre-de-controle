# Assumptions Table

| assumption_id | assumption | why needed | validation plan | fallback if invalid |
|---|---|---|---|---|
| ASSUMPTION-A1 | Baseline subscription can support workspace-only execution load | budget planning | 7-day telemetry simulation on pilot load | reduce concurrency and queue non-critical tasks |
| ASSUMPTION-A2 | Replay verification mostly reuses cached artifacts | CI budget planning | measure cache hit ratio during dual write | add artifact locality strategy and selective replay tiers |
| ASSUMPTION-A3 | Approval latency can stay below operational threshold | policy usability | instrument approval SLA and weekly review | pre-approve safe classes with strict limits |
| ASSUMPTION-A4 | Corruption detection overhead stays below 10 percent runtime | performance envelope | benchmark checksum path under stress | move heavy verification to async lane |
| ASSUMPTION-A5 | 40-dev staffing model remains available for 16 weeks | roadmap realism | staffing checkpoint each phase gate | de-scope P2 items and extend timeline |
| ASSUMPTION-A6 | Operator comprehension target of 60 seconds is realistic | UX acceptance | timed drills with incident cards | simplify card content and reduce metric noise |
| ASSUMPTION-A7 | Optional semantic layer is not required for initial stability goals | scope control | compare retrieval success FTS vs FTS+semantic | keep semantic disabled until measurable gain |
| ASSUMPTION-A8 | External dependency timeout profiles are stable enough for static retry classes | retry tuning | collect timeout histograms per service | adaptive timeout buckets per dependency |
