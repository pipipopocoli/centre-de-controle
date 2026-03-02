# Wizard Live (Wave19)

Goal: run a live text multiagent roundtable in Cockpit with one bundled headless run per turn.

## What it does
- Command surface: `#wizard-live start|run|stop`
- L1 roster (strict): `victor`, `leo`, `nova`, `vulgarisation`
- Session mode:
  - `start`: starts session and runs initial full-context turn
  - `run`: one-shot turn without changing session state
  - `stop`: stops session
- While session is active, each non-command operator message triggers one new turn.
- Every turn writes:
  - `BMAD/BRAINSTORM.md`
  - `BMAD/PRODUCT_BRIEF.md`
  - `BMAD/PRD.md`
  - `BMAD/ARCHITECTURE.md`
  - `BMAD/STORIES.md`
  - `runs/WIZARD_LIVE_<UTC>.json`
  - `runs/WIZARD_LIVE_<UTC>.md`
  - updates `STATE.md`, `ROADMAP.md`, `DECISIONS.md`

## Safety model
- One `codex exec` per turn with:
  - approval policy `never`
  - sandbox `read-only`
  - strict output schema validation
- Runtime policy default is API strict (`COCKPIT_RUNTIME_BACKEND=api`): desktop blocks local write actions in strict mode.
- No write in target repo. Writes are limited to Cockpit project data.

## Auto-kickoff
- Auto-start without popup:
  - after `New Project` intake flow
  - after Wave18 takeover wizard success

## UI usage
1. Open project in Cockpit.
2. Send `#wizard-live start`.
3. Continue chatting normally; each message runs one L1 bundle turn.
4. Send `#wizard-live stop` to end session.

## CLI usage
Start session:
```bash
./.venv/bin/python scripts/wizard_live.py start --project-id cockpit --repo-path /path/to/repo --data-dir app --trigger cli
```

One-shot run:
```bash
./.venv/bin/python scripts/wizard_live.py run --project-id cockpit --data-dir app --trigger cli --operator-message "focus risks"
```

Stop session:
```bash
./.venv/bin/python scripts/wizard_live.py stop --project-id cockpit --data-dir app --trigger cli
```

Each command prints a stable line:
```text
WizardLiveSummary status=... project_id=... run_id=... session_active=... output_json=...
```

## Troubleshooting
- If headless fails or output is invalid:
  - check `runs/WIZARD_LIVE_<UTC>_prompt.txt`
  - check `runs/WIZARD_LIVE_<UTC>.md`
  - rerun with `scripts/wizard_live.py run ...`

## Rollback
- Disable session immediately:
  - `#wizard-live stop`
  - or `scripts/wizard_live.py stop ...`
- Re-enable legacy local mode for maintenance only:
  - `COCKPIT_RUNTIME_BACKEND=local`
- Code rollback:
  - `git revert <wave19_commit_sha>`
  - `git push origin main`
