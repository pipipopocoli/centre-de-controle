# Paper Plan - CP-01 Next Steps V2

## Why this document
- Current checkpoint docs are valid, but too high-level for tight execution control.
- This plan is the detailed runbook for the next steps until checkpoint closure.
- Scope is strict: `control/projects/cockpit` only.

## Success target
- Close 10 issues in CP-01 with proof.
- Keep active WIP at 5 max at all times.
- Pass two smoke gates (after Wave 1 and after Wave 2).
- Publish final checkpoint snapshot and move phase to `Review`.

## Locked operating rules
- One issue = one owner = one delivery.
- Any blocker > 60 min: post 2 options + 1 recommendation.
- No Wave 2 work before explicit Wave 1 unlock.
- Every update in chat uses `Now / Next / Blockers`.

## Agent map and platforms
- `@victor` -> CDX lane owner.
- `@leo` -> AG lane owner.
- `@agent-1` -> CDX.
- `@agent-2` -> AG.
- `@agent-3` -> CDX.
- `@agent-4` -> AG.
- `@agent-5` -> CDX.
- `@agent-6` -> AG.
- `@agent-7` -> CDX.
- `@agent-8` -> AG.
- `@agent-9` -> CDX.
- `@agent-10` -> AG.

## Wave plan (detailed)

### Wave 1 (active now)
- Issues:
  - `ISSUE-CP-0001` owner `@agent-1` lead `@victor`
  - `ISSUE-CP-0002` owner `@agent-2` lead `@victor`
  - `ISSUE-CP-0003` owner `@agent-3` lead `@victor`
  - `ISSUE-CP-0011` owner `@agent-6` lead `@leo`
  - `ISSUE-CP-0012` owner `@agent-7` lead `@leo`
- Cadence:
  - `T+00`: assignment ack from each agent.
  - `T+45m`: first status.
  - `T+90m`: second status + risk check.
  - `T+120m`: first merge window.
  - `T+180m`: Wave 1 gate decision.

### Wave 1 gate checklist (must all pass)
- All 5 issues marked `Done` with evidence (diff + tests/logs/screens).
- No open blocker with severity high.
- Smoke suite passes:
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_basic.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_auto_mode.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_execution_router.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_loop.py`
- `STATE.md` updated with Wave 1 result.

### Wave 2 (starts only after Wave 1 gate)
- Issues:
  - `ISSUE-CP-0004` owner `@agent-4` lead `@victor`
  - `ISSUE-CP-0005` owner `@agent-5` lead `@victor`
  - `ISSUE-CP-0013` owner `@agent-8` lead `@leo`
  - `ISSUE-CP-0014` owner `@agent-9` lead `@leo`
  - `ISSUE-CP-0015` owner `@agent-10` lead `@leo`
- Cadence:
  - `T+00`: Wave 2 kickoff + assignment ack.
  - `T+45m`: status pass 1.
  - `T+90m`: status pass 2 + integration risk pass.
  - `T+150m`: merge window.
  - `T+210m`: final gate decision.

### Wave 2 gate checklist (must all pass)
- All 5 issues marked `Done` with evidence.
- QA evidence pack published for `ISSUE-CP-0015`.
- Full smoke suite passes:
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_basic.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_auto_mode.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_index.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_memory_compaction.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_execution_router.py`
  - `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_agent_loop.py`
- `ROADMAP.md` and `STATE.md` updated to `Review`.

## Merge strategy
- Every issue uses one focused branch and one PR.
- Merge order:
  - Backend core first: 0001 -> 0002 -> 0003
  - UI Wave 1 in parallel: 0011 and 0012
  - Wave 2 by dependency:
    - backend: 0004 then 0005
    - ui: 0013 then 0014 then 0015
- Rebase before merge if conflicts appear.
- No squash of unrelated issue commits.

## Blocker playbooks

### Playbook A - test failure in wave gate
- Option 1: hotfix in same issue branch.
- Option 2: split a dedicated fix issue and defer gate.
- Recommended: Option 1 if fix < 45 min, else Option 2.

### Playbook B - merge conflict across lanes
- Option 1: backend lead resolves and UI rebases.
- Option 2: UI lead resolves and backend rebases.
- Recommended: owner of conflicted target file resolves first.

### Playbook C - agent silent > 45 min
- Option 1: reminder and keep owner.
- Option 2: reassign to standby agent in same platform lane.
- Recommended: Option 1 once, then Option 2 at 60 min.

## Evidence package required per issue
- Diff link or patch summary.
- Test/log proof.
- Screenshot proof for UI issues.
- Final note: rollback path in one line.

## Final closure steps
- Publish `CHECKPOINT_CP01_FINAL_SNAPSHOT_<date>.md`.
- Post one summary in chat tagged `status`, `checkpoint`, `review`.
- Move phase from `Implement` to `Review`.
- Freeze CP-01 scope and open only post-checkpoint issues.
