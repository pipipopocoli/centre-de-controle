# Evidence - ASSUMPTION table with validation plan

| assumption_id | assumption | why needed now | validation plan | owner_role | target_milestone |
|---|---|---|---|---|---|
| ASSUMPTION-A1 | Global Brain promotion remains manual @clems approval in V2 | policy lock from prompt, not yet codified contract | policy tests + audit review with sample promotions | policy lead | M2 |
| ASSUMPTION-A2 | Retrieval ranking determinism can reach >=99.5 percent with fixed corpus | needed for replay gate | replay harness on frozen pack over 10 runs | QA lead | M3 |
| ASSUMPTION-A3 | Storage growth 15-30 GB/project/year under baseline retention | budget planning input | 30-day pilot telemetry extrapolation | SRE lead | M2 |
| ASSUMPTION-A4 | Chunk ids can be deterministic from hash(metadata+content) | reproducible references needed | collision and replay tests on synthetic corpus | backend lead | M1 |
| ASSUMPTION-A5 | Compaction can reduce storage by 25-45 percent | justify compaction complexity | A/B compaction benchmark across 3 project profiles | backend lead | M3 |
| ASSUMPTION-A6 | p95 lexical retrieval <=250ms at baseline load | gate threshold needed | load testing with fixed query sets | SRE lead | M2 |
| ASSUMPTION-A7 | Hybrid retrieval quality gain >=8 percent over lexical baseline | justify semantic layer cost | benchmark holdout set and compare p@k and recall@k | QA lead | M3 |
| ASSUMPTION-A8 | Program span around 4 months for memory lane | roadmap planning anchor | milestone burndown after M1/M2 | program lead | M2 |
| ASSUMPTION-A9 | Semantic token spend can be capped per project/day without major quality drop | budget safety | capped-vs-uncapped experiment on holdout set | ML lead | M3 |
| ASSUMPTION-A10 | Alert precision >0.8 is feasible for memory budget alarms | avoid alert fatigue | evaluate precision/recall on 4-week ops logs | SRE lead | M4 |
| ASSUMPTION-A11 | Aggregate storage envelope 5-15 TB for program horizon | infra reservation input | monthly capacity review and correction | SRE lead | M4 |
| ASSUMPTION-A12 | 60-second comprehension target is achievable for operators | UX acceptance bar | timed user tests on degraded scenarios | UX lead | M4 |
