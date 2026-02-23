# Wave14 dispatch packet - 2026-02-23

## Objective
- Make Cockpit operational for onboarding and managing a new existing repository with strict quality gates and stable runtime control.

## Source lock
- `/Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_INPUT_FROM_COCKPIT_V2_FINAL_PLAN_2026-02-23.md`

## Order + platform
1. @victor (CDX)
2. @leo (AG)
3. @nova (AG)
4. Wait 15m for lead ack (Now/Next/Blockers)
5. @agent-3 (CDX)
6. @agent-1 (AG)
7. @agent-6 (AG)
8. @agent-7 (AG)
9. @agent-11 (AG)

## Constraints
- WIP max = 5
- human validation before commit on critical lane
- existing repositories first
- codex + antigravity only (no extra fallback lane in Wave14)
- tournament remains dormant

## Prompt 1 - @victor (CDX)
```md
@victor
Objective
- Lead Wave14 backend/control lane: CP-0048, CP-0049, CP-0052.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/brain_manager.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_intake.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py
- /Users/oliviercloutier/Desktop/Cockpit/tests/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json

Scope (Out)
- tournament activation
- full UI redesign

Delegation
- @agent-3: deterministic healthcheck and gate tests
- @agent-1: startup onboarding flow checks + evidence path checks

Done
- startup pack onboarding for existing repo is deterministic
- mission-critical commit gate + evidence checklist enforced
- healthcheck false positives reduced with tests
- report every 2h in Now/Next/Blockers
```

## Prompt 2 - @leo (AG)
```md
@leo
Objective
- Lead Wave14 UI readability lane: CP-0051.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/

Scope (Out)
- backend routing internals
- tournament files

Delegation
- @agent-6: scenario matrix and repro
- @agent-7: screenshot mapping normal/degraded

Done
- compact live task squares visible and readable
- timeline focus is scope + wave + blockers
- simple view remains readable in <=2 min
- evidence pack mapped to scenario IDs
- report every 2h in Now/Next/Blockers
```

## Prompt 3 - @nova (AG)
```md
@nova
Objective
- Lead Wave14 memory/governance lane: CP-0050 + advisory for standard playbook.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/memory_index.py
- /Users/oliviercloutier/Desktop/Cockpit/app/data/store.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Scope (Out)
- tournament dispatch
- unrelated fallback provider work

Delegation
- @agent-11: retention readability pass + policy wording quality

Done
- retention policy documented and implementable: 7d/30d/90d/permanent archive
- no cross-project memory contamination path introduced
- standard playbook alignment: Intake -> Plan -> Clean -> Build -> Test -> Ship
- include one deep RnD recommendation with owner/action/evidence/decision_tag
- report every 2h in Now/Next/Blockers
```

## Prompt 4 - @agent-3 (CDX)
```md
@agent-3
Objective
- Add deterministic tests for mission-critical gates and healthcheck precision.

Done
- tests for degraded vs healthy semantics are deterministic
- false-positive scenarios covered with fixtures
- report Now/Next/Blockers
```

## Prompt 5 - @agent-1 (AG)
```md
@agent-1
Objective
- Validate startup pack onboarding path for existing repo and operator flow.

Done
- checklist verifies repo attach, startup pack generation, and no cross-project context leak
- report Now/Next/Blockers
```

## Prompt 6 - @agent-6 (AG)
```md
@agent-6
Objective
- Build Wave14 UI QA matrix for live task squares and timeline clarity.

Done
- full scenario table with repro/expected/verdict
- simple/tech and normal/degraded cases covered
- report Now/Next/Blockers
```

## Prompt 7 - @agent-7 (AG)
```md
@agent-7
Objective
- Produce screenshot evidence for Wave14 UI readability lane.

Done
- captures mapped by scenario id (normal + degraded)
- include hierarchy + timeline + live squares evidence
- report Now/Next/Blockers
```

## Prompt 8 - @agent-11 (AG)
```md
@agent-11
Objective
- Support Nova with retention policy wording and operator comprehension pass.

Done
- concise retention policy language validated
- operator can understand retention action in <=60s
- report Now/Next/Blockers
```
