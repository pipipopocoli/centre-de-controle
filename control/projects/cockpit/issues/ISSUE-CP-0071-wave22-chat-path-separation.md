# ISSUE-CP-0071 - Wave22 chat path separation

- Owner: agent-2
- Phase: Implement
- Status: In Progress
- Source: ai_auto

## Objective
- Lock direct vs room message rules, visible contribution rules, and legacy-history filtering.

## Done (Definition)
- [ ] Pixel Home shows only direct.
- [ ] Le Conseil shows only room.
- [ ] Legacy fake-success rows do not pollute visible logs.

## Risks
- History migration drift can still leak old rows into visible surfaces.
