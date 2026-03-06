# Wave16 Backend Onboarding + Recency Guard Lock

Timestamp (UTC): 2026-02-23T13:18Z
Lane: Victor backend

## Contract lock summary
- Onboarding UX contract locked with deterministic pack schema: `wave16_onboarding_pack_v1`.
- Canonical onboarding command path remains `scripts/project_intake.py`.
- Recency autopulse guard is explicit and opt-in (`--autopulse-guard`), with hard-failure skip semantics.
- Operator explicit pulse command path added: `scripts/auto_mode.py --pulse-only`.

## Verification commands (single pass)
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_onboarding_contract.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_recency_autopulse_guard.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave14_startup_pack.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave09_dual_root_cadence.py
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py
```

Output:
```text
OK: wave16 onboarding contract verified
OK: wave16 recency autopulse guard verified
OK: wave14 startup pack deterministic onboarding verified
OK: auto_mode healthcheck parity verified
OK: wave09 dual-root cadence verified
OK: wave07 control gate snapshot verified
```

## Onboarding pack sample (deterministic)
Sample command (temp root, no intake):
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/project_intake.py --repo-path <tmp_repo> --data-dir <tmp_projects_root> --no-run-intake --json
```

Observed sample:
```json
{
  "project_id": "sample-repo",
  "onboarding_pack_path": "/var/folders/.../projects/sample-repo/runs/onboarding_pack_latest.json",
  "schema_version": "wave16_onboarding_pack_v1",
  "keys": [
    "command_path",
    "issue_seed_paths",
    "project_dir",
    "project_id",
    "projects_root",
    "repo_path",
    "run_intake",
    "schema_version",
    "startup_pack_path"
  ],
  "run_intake": false
}
```

## Recency guard evidence (before/after)
Fixture: stale KPI snapshot + fresh pulse, no hard issues.

Before (no guard):
```json
{
  "code": 0,
  "status": "healthy",
  "issues": [],
  "warnings": ["stale_kpi_snapshot_soft"],
  "guard": {"attempted": false, "applied": false, "reason": "disabled"},
  "snapshot_age_seconds": 3300
}
```

After (`--autopulse-guard`):
```json
{
  "code": 0,
  "status": "healthy",
  "issues": [],
  "warnings": [],
  "guard": {"attempted": true, "applied": true, "reason": "snapshot_emitted"},
  "snapshot_age_seconds": 0
}
```

Hard-failure safety (covered by tests):
- With hard issues (ex: `pulse_stale`), guard is skipped with reason `hard_issues_present`.
- Exit code/status contract remains degraded on hard issues.

## Safety checks
```bash
git -C /Users/oliviercloutier/Desktop/Cockpit diff --name-only | rg tournament
```
Result: no output (no tournament path touched).

## Now / Next / Blockers
- Now: Wave16 backend lock done, onboarding pack contract + recency autopulse guard validated, tests green.
- Next: keep 2h cadence updates and monitor guard behavior on live cadence windows.
- Blockers: none.
