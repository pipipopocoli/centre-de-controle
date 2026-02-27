# Takeover Wizard (BMAD + L1 Roundtable)

Goal: stop "activating" @victor/@leo/@nova one by one.

This wizard generates, in 1 shot:
- BMAD artifacts (Product brief, PRD, Architecture, Stories)
- an L1 roundtable (Now/Next/Blockers per agent)
- updates to STATE/ROADMAP/DECISIONS + a run log

Wave19 adds a live mode for continuous turns in chat:
- see `docs/WIZARD_LIVE.md`
- command: `#wizard-live start|run|stop`
- auto-kickoff runs after new project onboarding and after takeover success

Default output location: `~/Library/Application Support/Cockpit/projects/<project_id>/`.

## UI (recommended)
1. Open Cockpit and select a project.
2. Click `Takeover Wizard`.
3. If the project is not linked, pick the repo folder.
4. Confirm the cost popup.

Chat trigger:
- Send `#wizard` (or type "lance le wizard") and confirm.

## CLI
Prereq: you must be logged in once:
```
codex login
```

Run (headless):
```
./.venv/bin/python scripts/takeover_wizard.py --repo-path /path/to/repo --data-dir app --headless --run-intake
```

Prompt only (no headless):
```
./.venv/bin/python scripts/takeover_wizard.py --repo-path /path/to/repo --data-dir app --no-run-intake
```

## Outputs (per project)
- `BMAD/PRODUCT_BRIEF.md`
- `BMAD/PRD.md`
- `BMAD/ARCHITECTURE.md`
- `BMAD/STORIES.md`
- `runs/TAKEOVER_WIZARD_<UTC>.json` (normalized output)
- `runs/TAKEOVER_WIZARD_<UTC>.md` (evidence log)
- `runs/TAKEOVER_WIZARD_<UTC>_prompt.txt` (the exact prompt used)

## Safety model (V1)
- Headless is 1x `codex exec` with sandbox `read-only`.
- The wizard must not modify the target repo.
- The wizard writes only inside the Cockpit project data dir.

## Wave18 vs Wave19
- Wave18 takeover wizard: one-shot kickoff.
- Wave19 wizard live: session-based live text roundtable with one bundled run per operator turn.

## Troubleshooting
- If headless fails: open the `*_prompt.txt` path from the run log and run it manually in Codex.
- If UI looks stale after a wizard run: hit `Refresh` or restart the app.
