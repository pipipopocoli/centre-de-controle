# Issue Map - Wave04 CP-002x

## Active issues in this wave
- ISSUE-CP-0021 - Wave04 control loop cadence (owner: clems)
- ISSUE-CP-0022 - Wave04 UI ship lock (owner: leo)
- ISSUE-CP-0023 - Wave04 backend contract lock (owner: victor)
- ISSUE-CP-0024 - Wave04 cleanup canonicalization (owner: agent-11)
- ISSUE-CP-0025 - Wave04 dispatch pack and operator packet (owner: clems)

## Dependency graph
- CP-0021 independent, must run all wave.
- CP-0022 independent from CP-0023.
- CP-0023 independent from CP-0022.
- CP-0024 non-blocking for Gate 1, required before final cleanup signoff.
- CP-0025 depends on progress evidence from CP-0021/0022/0023.

## Gate ownership
- Gate 1 (T+120): clems + victor + leo
- Gate 2 (T+240): clems final decision
