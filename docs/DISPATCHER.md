# Dispatcher (Auto-mode)

The dispatcher reads run requests and writes per-agent inbox files.

## What it does
- Reads: `control/projects/<project_id>/runs/requests.ndjson`
- Writes: `control/projects/<project_id>/runs/inbox/<agent_id>.ndjson`
- Dedupes by `request_id` using `runs/dispatch_state.json`
- Ignores requests with `source="reminder"`

## Run once
```
./.venv/bin/python scripts/dispatcher.py --project cockpit --once
```

## Run continuously
```
./.venv/bin/python scripts/dispatcher.py --project cockpit --interval 5
```

## Notes
- This does not create Antigravity threads by itself.
- Agents (or an external runner) must read their inbox file to act.
- The state file prevents re-dispatch on restart.
