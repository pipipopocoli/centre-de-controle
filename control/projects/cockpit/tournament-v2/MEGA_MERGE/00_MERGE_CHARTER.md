# 00_MERGE_CHARTER

## Mission
- Build one canonical `MEGA_PLAN_V2` from all six R1 competitors with zero overlap and zero unresolved architectural conflicts.
- Produce an implementation-ready package that can be dispatched to execution streams without additional design decisions.

## Inputs
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-a/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-b/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-c/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-d/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-f/

## Non-negotiable constraints
- Global Brain is accessible for generic skills, souls, protocols, and learnings only.
- Project memory stays isolated by default. No cross-project retrieval for project logs/artifacts/conversations.
- Souls Option A is fixed:
  - Persistent: clems (L0), victor (L1), leo (L1).
  - Workers: ephemeral and project-scoped.
- Skills are executable in V2, workspace-only by default.
- Full access actions require explicit @clems approval.
- Priority order for arbitration:
  1. stability
  2. engineering quality
  3. operator clarity
  4. resource feasibility

## Layer model (locked)
- L1 Reliability core (owner: competitor-r1-a)
- L2 Skills supply chain + governance (owner: competitor-r1-b)
- L3 Router/orchestration multi-agents (owner: competitor-r1-c)
- L4 Memory engine + isolation (owner: competitor-r1-d)
- L5 Eval harness + non-regression (owner: competitor-r1-e)
- L6 UX vulgarisation + operator flow (owner: competitor-r1-f)
- L7 Resource/cost/capacity (owner: competitor-r1-b)

## Anti-overlap contract
- Each capability must have one and only one `capability_id`.
- Each `capability_id` must have exactly one `owner_layer`.
- All non-owner contributions are listed under `imports[]` only.
- Any design conflict must be resolved using one status only:
  - adopt
  - reject
  - defer
- No section is accepted into final plan without `capability_id` reference.

## Decision governance
- Decision unit: `capability_id`.
- Required fields per decision:
  - owner
  - imports
  - status
  - rationale
  - test_gate
- Conflict resolution log is mandatory and auditable.

## Quality gates
- G0: Source completeness gate
  - all six R1 packages present
- G1: Layer ownership gate
  - one owner per layer, no duplicates
- G2: Capability overlap gate
  - zero duplicate ownership per capability
- G3: Constraint compliance gate
  - full-access and memory isolation constraints intact
- G4: Implementation readiness gate
  - each stream has DoD + verification evidence
- G5: Operator readability gate
  - summary page understandable in <=60 seconds

## Deliverables
- 01_LAYER_OWNERSHIP_MATRIX.md
- 02_CAPABILITY_REGISTRY.md
- 03_CONFLICT_RESOLUTION_LOG.md
- 04_MEGA_PLAN_V2_FINAL.md
- 05_IMPLEMENTATION_PROMPT_PACK.md
- 06_OPERATOR_SUMMARY.html

## Done criteria
- One canonical mega plan exists with no unresolved architectural decision.
- Every major contract maps to a unique `capability_id`.
- Every conflict has a logged final status and rationale.
- Implementation prompts can be dispatched immediately with no missing decision.
