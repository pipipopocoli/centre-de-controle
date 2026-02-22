# Claim Trace Matrix

| claim_id | major claim | evidence | fallback if unproven |
|---|---|---|---|
| C1 | Deterministic replay requires ordered event logs plus snapshot boundaries. | P1, P2, P3 | Freeze release gate and ship with replay disabled flag. |
| C2 | Tail latency dominates perceived reliability under operator pressure. | P6 | Add stricter p99 SLO and lower refresh cadence. |
| C3 | Distributed tracing style correlation IDs improve incident navigation. | P5, S1 | Keep minimal event linking via run_id only. |
| C4 | Scheduler fairness and anti-herd controls are mandatory for multi-agent stability. | P7, R1, R8 | Add static priority queues and hard concurrency caps. |
| C5 | Situation awareness model supports one-screen summary first, details second. | P8, ASSUMPTION-A2 | Expand training and simplify card set to top 4 signals. |
| C6 | Position and length encodings reduce chart misreads compared to decorative alternatives. | P9, ASSUMPTION-A9 | Replace weak visuals with table fallback in high pressure mode. |
| C7 | Project isolation with explicit promotion gate prevents contamination risk. | Locked constraints, ASSUMPTION-A11 | Lock promotion feature until policy workflow is complete. |
| C8 | Workspace-only skill execution and lockfile pinning reduce supply-chain risk. | R4, S3, SKILLS_V0_SPEC | Disable external skills by default until audit passes. |
| C9 | Offline-first HTML dashboard reduces operational dependency risk. | VULGARISATION_TAB_SPEC, ASSUMPTION-A12 | Provide static snapshot export from CI as fallback. |
| C10 | FTS-first memory stack is enough for V2 and can later add semantic layer. | R2, R3, ASSUMPTION-A4, ASSUMPTION-A5 | Move semantic layer to optional experiment workstream only. |
