# Issue Map - Wave09 CP-0035..0038

## Active issues
- ISSUE-CP-0035 - dual-root control cadence (owner: victor)
- ISSUE-CP-0036 - healthcheck contract hardening (owner: agent-3)
- ISSUE-CP-0037 - pilotage control badges (owner: leo)
- ISSUE-CP-0038 - advisory closeout ledger (owner: nova)

## Dependencies
- CP-0036 depends on baseline parity behavior from CP-0035.
- CP-0037 depends on stable dual-root status output from CP-0035/CP-0036.
- CP-0038 depends on latest gate states from CP-0035..CP-0037.

## Gate ownership
- Gate 1 (T+120): clems + victor
- Gate 2 (T+240): clems + victor + leo
- Closeout (T+360): clems + nova
