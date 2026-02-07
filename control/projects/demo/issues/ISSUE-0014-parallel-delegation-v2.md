# ISSUE-0014 - Parallel delegation (agent-N specialists) (V2.2.1)

- Owner: clems
- Phase: Review
- Status: Review

## Objective
- Allow leads (Victor/Leo) to delegate work to specialists named `agent-1`, `agent-2`, ... via mentions, even if the specialist is not in the roster yet.

## Scope (In)
- Mentions parsing accepts: @clems @victor @leo + @agent-<number>.
- Alias: @clem -> @clems.
- record_mentions writes a run request for each mention (even if agent not in roster).
- Auto-reply shows visible action line: "Action: ping @agent-1".
- Add a verification script.

## Scope (Out)
- Auto-creation of agent files for agent-N.
- Scheduler/daemon.
- Full routing/assignment AI.

## Now
- Implement mention policy + run request emission.

## Next
- Manual QA in app: ping @agent-1 -> run request written + action visible.

## Blockers
- None.

## Done (Definition)
- Typing "Ping @agent-1" creates a run request NDJSON.
- No auto-create of agent directories for agent-1.
- Clems reply includes an explicit action line.
- `./.venv/bin/python tests/verify_specialists.py` passes.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Mention filter too strict or too loose.
- Reminder loops if run requests are re-emitted.
