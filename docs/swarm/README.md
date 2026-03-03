# Swarm Auditor v2

Goal: scan the repo (code + config + docs) and produce:
- prioritized issues (p0-p3)
- blocking/clarifying questions
- small proposed diffs (optional)

Outputs (commit-friendly) land in `docs/swarm/`:
- `latest_report.md`
- `latest_questions.md`
- `latest_summary.json`
- `latest_big_push.md` (LLM plan-of-attack, best effort)
- `latest_diffs.patch` (only when enabled)

Raw run data is local-only (gitignored):
- `docs/swarm/_runs/<run_id>/raw.ndjson`
- `docs/swarm/_runs/<run_id>/meta.json`
- `docs/swarm/_cache/index.json`

## Setup

Install deps:
```bash
python3 -m pip install -r scripts/swarm/requirements_swarm.txt
```

Set OpenRouter key:
```bash
export COCKPIT_OPENROUTER_API_KEY="..."
```

## Run

Dry run (no API calls, no key required):
```bash
python3 scripts/swarm/swarm_auditor.py --dry-run
```

Full run (writes to `docs/swarm/`):
```bash
python3 scripts/swarm/swarm_auditor.py
```

Emit patch file too:
```bash
python3 scripts/swarm/swarm_auditor.py --emit-patch-file
```

Consolidate a specific run:
```bash
python3 scripts/swarm/swarm_consolidator.py --in docs/swarm/_runs/<run_id>/raw.ndjson --out-dir docs/swarm
```

Patch apply check (no auto-apply):
```bash
python3 scripts/swarm/swarm_consolidator.py --in docs/swarm/_runs/<run_id>/raw.ndjson --out-dir docs/swarm --emit-patch-file --git-apply-check
```

