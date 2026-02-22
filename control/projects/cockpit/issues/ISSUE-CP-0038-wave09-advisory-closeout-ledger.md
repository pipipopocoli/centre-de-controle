# ISSUE-CP-0038 - Wave09 advisory closeout ledger

- Owner: nova
- Phase: Implement
- Status: Done

## Objective
- Publish a Wave09 advisory summary that is operator-first and action-ready.
- Maintain an accepted/deferred/rejected ledger with owner/action/evidence traceability.
- Add continuous RnD scouting outputs (code/literature/technology watch) at each project phase.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_VULGARISATION_UPGRADE_WAVE07.md`

## Scope (Out)
- Direct backend code edits
- UI widget edits
- Tournament dispatch

## Done (Definition)
- [x] Brief 60s explicitly reports dual-root status.
- [x] Top 3 residual risks have concrete mitigation.
- [x] Deferred debt reminder includes `CP-0015` as non-blocking.
- [x] Advisory ledger lists accepted/deferred/rejected with evidence links.
- [x] At least one deep RnD item is published per checkpoint.

## Closeout Advisory Packet

### Brief 60s
- On est ou: Wave09 is in Implement; CP-0035 dual-root cadence is shipped; repo and AppSupport are healthy across two consecutive checkpoints.
- On va ou: finish CP-0036 deterministic healthcheck hardening and keep the 25-30 minute cadence as the active control baseline.
- Pourquoi: stale snapshot semantics can still drift over elapsed time and trigger false degraded even when queue signals stay healthy.
- Comment: keep pulse plus healthcheck cadence strict, run owner-routed advisory decisions with evidence, and carry one deep RnD item into next sprint.

### Advisory Ledger (accepted/rejected/deferred)
LID:W09-L1 | status:accepted | owner:@victor | next_action:finalize CP-0036 deterministic stale semantics using Wave09 cadence constants | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DECISION_2026-02-20T2148Z.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md | updated_at:2026-02-20T22:21:09Z
LID:W09-L2 | status:rejected | owner:@clems | next_action:keep tournament auto-dispatch disabled during active implementation lanes | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md | updated_at:2026-02-20T22:21:09Z
LID:W09-L3 | status:deferred | owner:@leo | next_action:reopen docs embed scope through ISSUE-CP-0015 after Wave09 closeout | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0015-ui-integrate-html-docs.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md | updated_at:2026-02-20T22:21:09Z

### Top 3 Residual Risks + Mitigation
R1 | risk:stale_kpi_snapshot can regress if CP-0036 does not lock elapsed-time behavior | mitigation:ship CP-0036 test matrix and keep max_snapshot_age_seconds checks active | owner:@victor | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0036-wave09-healthcheck-contract-hardening.md
R2 | risk:operator cadence drift can reintroduce false degraded windows | mitigation:enforce 25-30 minute runbook and keep dual-root checks in every active window | owner:@clems | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md
R3 | risk:operator clarity can drift if repo/app signals are not reviewed together | mitigation:retain dual-root status wording and keep CP-0037 evidence mapping in closeout reviews | owner:@leo | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0037-wave09-pilotage-control-badges.md

### Deep RnD Recommendation for Next Sprint
D1 | recommendation:Adaptive KPI recency contract with dual-threshold confidence band. | owner:@victor | next_action:In next sprint, add an experiment matrix in healthcheck tests to compare fixed 2100s vs adaptive threshold driven by recent pulse interval variance. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md | success_signal:No false stale_kpi_snapshot over two windows while preserving detection of true stale incidents.

### Deferred debt reminder
- `ISSUE-CP-0015` stays deferred and non-blocking for Wave09 closeout.
- Reopen only when docs embed scope is explicitly reactivated.

## Closeout Evidence
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DECISION_2026-02-20T2148Z.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0015-ui-integrate-html-docs.md`

## Test/QA
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_comprehension.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md`
