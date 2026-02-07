# Auto-mode (Runner)

Auto-mode turns Cockpit run requests into actionable inbox items and helps you launch the right app.

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

## Run once
```
./.venv/bin/python scripts/auto_mode.py --project demo --once
```

## Run continuously
```
./.venv/bin/python scripts/auto_mode.py --project demo --interval 5
```

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

