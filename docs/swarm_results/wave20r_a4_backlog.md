# Wave20R A4 Backlog

- Mission: Provider descope + OpenRouter-only migration on app services
- Scope allowlist: app/services/execution_router.py, app/services/agent_registry.py, app/services/task_matcher.py, app/data/store.py, app/services/wizard_live.py, app/services/takeover_wizard.py, app/services/codex_runner.py, app/services/antigravity_runner.py, app/schemas/takeover_wizard_output.schema.json
- Source trackers: docs/swarm_results/wave1_p0p1_tracker.md, docs/swarm_results/wave2_p2_tracker.md, docs/swarm_results/wave2_p3_tracker.md, docs/swarm_results/wave20_unassigned_backlog.md
- Initial rows: 6

| issue_id | source | severity | file | status_before | action | evidence_command | evidence_result | reason_code | note |
|---|---|---|---|---|---|---|---|---|---|
| `ISSUE-W1-T1-001` | `docs/swarm_results/wave1_p0p1_tracker.md` | `P0` | `app/data/store.py` | `defer` | `done` | `grep -A 2 '"platform":' app/data/store.py \` | `head -10` | `platform: "openrouter"` | `` |
| `ISSUE-W1-T1-002` | `docs/swarm_results/wave1_p0p1_tracker.md` | `P0` | `app/data/store.py` | `defer` | `done` | `grep '"engine":' app/data/store.py \` | `head -5` | `"engine": "OR"` | `` |
| `ISSUE-W2-P2-T1-018` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `app/data/store.py` | `defer` | `done` | `python3 -c "import app.data.store; print('openrouter' in [a['platform'] for a in app.data.store.DEFAULT_AGENT_ROSTER])"` | `True` | `` | Verified all agents use openrouter platform |
| `ISSUE-W2-P2-T3-075` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `app/schemas/takeover_wizard_output.schema.json` | `defer` | `defer` | `python3 -c "import json; f=open('app/schemas/takeover_wizard_output.schema.json'); json.load(f); print('valid')"` | `valid` | `non_repro` | Schema validates as valid JSON; no specific reproduction steps provided in source tracker |
| `ISSUE-W2-P2-T3-076` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `app/schemas/takeover_wizard_output.schema.json` | `defer` | `defer` | `python3 -m json.tool app/schemas/takeover_wizard_output.schema.json > /dev/null && echo "valid json"` | `valid json` | `non_repro` | No specific validation errors identified; schema conforms to draft-07 |
| `ISSUE-W2-P3-T3-054` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `app/schemas/takeover_wizard_output.schema.json` | `defer` | `defer` | `python3 -c "import jsonschema; jsonschema.Draft7Validator.check_schema(json.load(open('app/schemas/takeover_wizard_output.schema.json')))" 2>&1 \` | `\` | `stale` | `check completed` |
