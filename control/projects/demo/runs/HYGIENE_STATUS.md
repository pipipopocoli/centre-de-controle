# Runloop Hygiene Status

Timestamp (UTC)
- 2026-02-08T09:00:59+00:00

Now
- Single writer enforced: auto_mode_state.json is source of truth.
- dispatch_state.json disabled and read-only.
- requests.ndjson compacted (last-write-wins).
- Inbox rebuilt from open runtime requests only.
- Periodic hygiene runner active every 10 minutes.

Acceptance Snapshot
- REQ_DUP_LINES: 0
- REQ_OLD_ROWS_GT24H: 0
- RUNTIME_OPEN_OLD_GT24H: 0
- INBOX_DUP_LINES: 0
- skipped_duplicate_delta: 78

Healthcheck
- No reminder/duplicate noise issue.
- Remaining degraded reason: close_rate_low (expected until agents reply to open requests).

Schedule
- cron: */10 * * * * /usr/bin/python3 control/projects/demo/runs/runloop_hygiene.py --project demo

Artifacts
- control/projects/demo/runs/runloop_hygiene.py
- control/projects/demo/runs/hygiene.log.ndjson
- control/projects/demo/runs/hygiene_guardrail_state.json
