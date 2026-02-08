# State
## Phase
- Test
## Objective
- Verify runloop lifecycle queued -> dispatched -> replied/done with close_rate_24h >= 90%
## Now
- agent-3 lifecycle verification done on 3 e2e tests
- close_rate_24h gate validated on KPI scenario
## Next
- Monitor runloop after push and rerun e2e after auto_mode changes
- Keep stale/reminder checks active
## In Progress
- Runloop stabilization and verification
## Blockers
- None
## Risks
- Runloop regressions if lifecycle hooks drift in mcp/auto_mode
- Reminder noise can rise if inbox dedupe drifts
## Links
- ROADMAP.md
- DECISIONS.md
- tests/verify_auto_mode.py
- tests/verify_run_loop_kpi.py
- tests/verify_agent_loop.py
