# Issue Map - Wave05 CP-0026..0032

## Active issues
- ISSUE-CP-0026 - agent registry runtime (owner: victor)
- ISSUE-CP-0027 - platform mapping from registry (owner: agent-1)
- ISSUE-CP-0028 - task scoring engine (owner: agent-3)
- ISSUE-CP-0029 - dispatch backpressure (owner: victor)
- ISSUE-CP-0030 - router tiered fallback (owner: victor)
- ISSUE-CP-0031 - cost telemetry CAD (owner: agent-11)
- ISSUE-CP-0032 - SLO gates (owner: leo)

## Dependencies
- CP-0027 depends on CP-0026 registry shape.
- CP-0028 can start in parallel with CP-0026 and join in auto_mode.
- CP-0029 depends on CP-0028 integration in dispatch lane.
- CP-0030 can run in parallel with CP-0026/28.
- CP-0031 depends on CP-0030 event emission.
- CP-0032 depends on CP-0031 metrics artifacts.

## Gate ownership
- Gate 1 (T+120): clems + victor
- Gate 2 (T+240): clems + victor + leo
- Closeout (T+360): clems
