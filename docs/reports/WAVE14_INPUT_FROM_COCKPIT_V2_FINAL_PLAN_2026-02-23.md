# Wave14 Input - Cockpit V2 Final Plan (2026-02-23)

## Source
- `/Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx`

## Locked product intent
1. Functional cockpit means:
- clear UI (no clutter/overlap)
- seamless repo connection
- full project + messaging management
- clear startup process for new projects

2. Target project types (priority now)
- existing repositories first:
  - web apps
  - backend APIs
  - desktop apps
  - data projects

3. Human validation policy
- plan for each wave approved before execution
- no commit without human validation
- after each wave: review and adjustments by clems

4. Role model
- L0: clems
- L1: victor (backend), leo (ui), nova (vulgarisation + RnD)
- L2: specialists under L1
- dynamic L1 extension allowed if needed

5. Priorities order
- cost control
- operator readability
- run stability
- speed after above

6. Model policy (for now)
- codex + antigravity only
- no fallback providers in active lane now

7. UX expectations
- live task status visualization (small status squares acceptable)
- vulgarisation readable in < 2 min
- timeline focused on scope, active wave, and task state

8. Mission critical and quality gates
- blockers must be resolved before progressing critical tasks
- quality evidence requires:
  - tests
  - screenshots
  - logs
  - docs update

9. Multi-project and memory
- multiple projects concurrently
- strict project memory isolation
- retention policy:
  - 7 days
  - 30 days
  - 90 days
  - permanent compressed archive

10. Healthcheck objective
- zero false positives target for operational alerts

11. Standard execution playbook
- Intake -> Plan -> Clean -> Build -> Test -> Ship

## Wave14 translation
- Wave14 objective: make cockpit operational on a new existing repo with strict gate control and zero cross-project contamination.
- Scope split:
  - startup pack + repo attach
  - mission critical commit gate
  - healthcheck false-positive hardening
  - live task squares and timeline readability
  - memory retention policy implementation
