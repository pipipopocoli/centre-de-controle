# ISSUE MAP - WAVE16 (CP-0056..CP-0060)

## Objective
- Run a codex-only consolidation wave while Antigravity is unavailable, close in-flight backend/advisory work, and keep runtime healthy with strict credit guard.

## Issues
1. CP-0056 - codex-only outage mode lock (owner: victor)
2. CP-0057 - dirty tree consolidation + push (owner: clems)
3. CP-0058 - credit guard dispatch policy (owner: victor)
4. CP-0059 - dual-root recency ops cadence (owner: victor)
5. CP-0060 - nova retention operator digest (owner: nova)

## Constraints
- WIP max = 5
- lead-first dispatch
- Codex-only operations until AG returns
- no tournament activation
- reserve floor >= 350 credits until Feb 26
