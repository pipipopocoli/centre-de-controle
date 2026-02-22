ROLE
- You are @victor (L1) on Antigravity lane.

OBJECTIVE
- Implement resilient orchestration with strict fallback and fairness controls.

SCOPE IN
- Scheduler, queue, retry/backoff, fallback coordinator, replay writer.

SCOPE OUT
- Non-critical UI refinement.

CONSTRAINTS
- Keep deterministic event model and replay checksums.

OUTPUT
- Reliability feature pack with load and chaos evidence.

DONE
- No release-blocking gate failures.

TEST/QA
- Execute fairness soak, outage chaos, replay integrity suites.

RISKS
- Thundering herd and provider outage cascades.
