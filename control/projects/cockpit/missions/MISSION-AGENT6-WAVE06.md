# Mission - Agent 6 (Nova) - Wave 6

## Objective
- Take ownership of L1 creative/reasoning layer.
- Ensure all timeline events are strictly ordered.

## Protocol
1.  **Global L1:** Intercept all broad queries. Route specialized tasks to legacy agents only when confident.
2.  **Timeline Guard:** Ensure `ts_iso` is monotonic for generated events.

## Deliverables
- `ISSUE-CP-0033` (This mission)
- `agents/nova/journal.ndjson` (Active logs)

## Constraints
- Do not modify `app/ui` without explicit CP-001x approval.
