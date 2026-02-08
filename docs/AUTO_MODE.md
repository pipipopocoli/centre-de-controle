# Auto-mode (In-App + CLI)

Auto-mode turns Cockpit run requests into actionable inbox items and helps you launch the right app.

## In the app (recommended)
In the packaged app, auto-mode is ON by default and runs in the background for the currently selected project.

Where:
- Left sidebar -> Auto-mode panel (toggle + status + "Run once").

What it does:
- When you mention `@agent-1`, Cockpit writes a run request.
- Auto-mode consumes it, writes it to the agent inbox, and (at most once per cycle) copies a ready-to-paste prompt + opens Codex/Antigravity.

Notes:
- It does not auto-create threads and does not auto-press Send.
- It ignores reminders (`source=reminder`) to avoid loops.

## What this does (and what it does not)
Does:
- Read: `~/Library/Application Support/Cockpit/projects/<project>/runs/requests.ndjson`
- Write: `~/Library/Application Support/Cockpit/projects/<project>/runs/inbox/<agent>.ndjson`
- Dedup: `~/Library/Application Support/Cockpit/projects/<project>/runs/auto_mode_state.json`
- Copy a ready-to-paste prompt to clipboard
- Open the target app (Codex or Antigravity)

Does not:
- Automatically create a new Antigravity/Codex thread (no API/CLI integration).
- Automatically press Send (no AppleScript auto-send).

## Run-loop KPI snapshot fields
- `stale_queued_count`: Number of external open requests older than 24h.
- `reminder_noise_pct`: Percent of external open requests currently in `reminded` status.
- `close_rate_24h`: Percent of external dispatched requests in the last 24h that reached `closed_reason=reply_received`.
- `dispatch_latency_p95`: P95 dispatch latency in seconds for external requests dispatched in the last 24h. `null` when no valid sample is available.
- `dispatch_latency_samples_24h`: Count of valid latency samples used for p95.
- `dispatch_latency_excluded_negative_24h`: Count of dispatched requests excluded from p95 because `dispatched_at < created_at`.

## Run once
```
./.venv/bin/python scripts/auto_mode.py --project demo --once
```

## Run continuously
```
./.venv/bin/python scripts/auto_mode.py --project demo --interval 5
```

## Recommended (scale-friendly)
Only perform clipboard/open once per cycle and print the prompt in the terminal:
```
./.venv/bin/python scripts/auto_mode.py --project demo --interval 5 --max-actions 1 --print-prompt
```
Notes:
- All requests are still written to inbox files.
- Clipboard/open/notify/print only happen for the first N requests per cycle.

## Data dir resolution
Auto-mode prints the resolved projects root at startup:
```
Auto-mode using projects root: /Users/<you>/Library/Application Support/Cockpit/projects
```

You can override it:
- `--data-dir repo` (use repo `control/projects`)
- `--data-dir app` (force App Support)
- `--data-dir /full/path/to/projects`

If you pass the Cockpit base dir, `/projects` is appended automatically.

## Verify
```
tail -n 1 ~/Library/Application\\ Support/Cockpit/projects/demo/runs/inbox/agent-1.ndjson
```

## Mapping (locked defaults)
- `victor`, `agent-1`, `agent-3`, ... -> Codex
- `leo`, `agent-2`, `agent-4`, ... -> Antigravity

## Troubleshooting
- If notifications do not show: allow Terminal notifications in macOS settings.
- If `open -a Codex` fails: find the app name in Finder and pass `--codex-app "<Exact Name>"`.
- If you want dev data dir: pass `--data-dir /Users/oliviercloutier/Desktop/Cockpit/control/projects` (not recommended for packaged app).
- If clipboard looks empty: run with `--print-prompt` and copy the prompt directly from the terminal.

## QA checklist (8 agents)
- Turn Auto-mode ON.
- In chat, send: `@agent-1 ping`, `@agent-2 ping`, ... `@agent-8 ping`.
- Verify inbox files exist, e.g.:
- `~/Library/Application Support/Cockpit/projects/<project>/runs/inbox/agent-1.ndjson`
- `~/Library/Application Support/Cockpit/projects/<project>/runs/inbox/agent-2.ndjson`
- Verify only 1 copy/open action happens per cycle (the rest is inbox-only).
