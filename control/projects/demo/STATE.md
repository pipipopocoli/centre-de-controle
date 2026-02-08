# State
## Phase
- Test
## Objective
- Keep runloop hygiene stable (anti-noise) while improving close_rate_24h with real agent replies.
## Now
- runloop anti-noise applied in run files with single writer and guardrails
- requests compaction + inbox rebuild completed (req dup=0, old_rows_gt24h=0, inbox dup=0)
- dispatch_state.json disabled/read-only to avoid dual dispatch path
## Next
- monitor close_rate_24h and clear open requests via agent replies
- keep periodic hygiene active every 10 minutes and watch guardrail logs
## In Progress
- Runloop hygiene autopilot + KPI monitoring
## Blockers
- close_rate_24h is still below target until agents post replies on open requests
## Risks
- Runloop regressions if lifecycle hooks drift in mcp/auto_mode
- Reminder noise can rise if inbox dedupe drifts
## Links
- ROADMAP.md
- DECISIONS.md
- control/projects/demo/runs/runloop_hygiene.py
- control/projects/demo/runs/hygiene.log.ndjson
- tests/verify_auto_mode.py
- tests/verify_run_loop_kpi.py
- tests/verify_agent_loop.py
