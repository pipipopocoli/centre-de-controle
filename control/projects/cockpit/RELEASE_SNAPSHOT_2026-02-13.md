# Release Snapshot - 2026-02-13

## Scope
- Project: `cockpit`
- Baseline: `origin/main` at `8e51711`
- Artifact: `dist/Centre de controle.app`

## Ship Gate Matrix

1. Scenario 1 - Dock target
- Check: `defaults read com.apple.dock persistent-apps`
- Result: PASS
- Evidence: `_CFURLString` contains `file:///Users/oliviercloutier/Desktop/Cockpit/dist/Centre%20de%20controle.app/`

2. Scenario 2 - Cold start + chat core flow
- Check A: launch packaged binary for 6 seconds (`dist/Centre de controle.app/Contents/MacOS/Centre de controle`)
- Result A: PASS (`alive_after_6s=true`, no stderr crash)
- Check B: load project and chat channels (`global`, `status`, `runloop`, `packaging`)
- Result B: PASS (`chat_core_ok=true`)

3. Scenario 3 - Mention flow single ack
- Action: operator posted `QA mention flow check 20260213T144521Z: Ping @leo`
- Result: PASS
- Evidence: exactly one new `mention_ack` event with text `Mentions: @leo`
- Run request created: `runreq_20260213144521.6937480000_leo_msg_20260213_144521_operator`

## Agent Status Posts
- @victor posted `Now/Next/Blockers` in `chat/global.ndjson` and `threads/status.ndjson`
- @leo posted `Now/Next/Blockers` in `chat/global.ndjson` and `threads/status.ndjson`
- Agent states updated to `phase=Ship`, `percent=100`, `status=completed` for `victor` and `leo`

## Ship Decision
- Gate status: GREEN
- Decision: Move project `cockpit` to `Ship`
- Owner: @clems

## Rollback
- App-level rollback: revert baseline commit chain on main if regression appears.
- Operational rollback: pin Dock shortcut to previous known-good packaged app in `dist/_archive` if needed.
