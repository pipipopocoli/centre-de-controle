# Tournament V2 Pack - Operator Runbook

## 0) Pack index
This folder contains:
- TOURNAMENT_PROMPT_R1.md
- TOURNAMENT_PROMPT_R2.md
- TEMPLATE_PLAN_40DEVS.md
- RUBRIC_SCORE.md
- SKILLS_V0_SPEC.md
- VULGARISATION_TAB_SPEC.md
- COST_MODEL_NOTE.md
- SKILLS_REPO_SHORTLIST.md

## 1) Tournament format
- R1: 6 competitors isolated.
- R2: top 4 finalists, full visibility on R1 outputs.
- Goal: choose final plan before implementation.

## 2) R1 launch checklist (pre-launch)
- Confirm locked constraints are included in prompt.
- Confirm output root exists:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/`
- Confirm each competitor has unique output folder.
- Confirm evidence floor is stated.

## 3) R1 execution steps
1. Send each competitor the generic R1 prompt + assigned axis variant.
2. Ensure competitor writes only in its own folder.
3. Collect outputs when all 10 required artifacts are present.
4. Score with `RUBRIC_SCORE.md`.
5. Rank top 4.

## 4) R1 output locations
- competitor-r1-a: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-a/`
- competitor-r1-b: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-b/`
- competitor-r1-c: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-c/`
- competitor-r1-d: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-d/`
- competitor-r1-e: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/`
- competitor-r1-f: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-f/`

## 5) R2 launch checklist (pre-launch)
- Confirm top 4 selected and locked.
- Confirm R1 outputs are readable.
- Confirm output root exists:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2/`
- Confirm R2 finalists know merge/arbitration rules.

## 6) R2 execution steps
1. Dispatch `TOURNAMENT_PROMPT_R2.md` to each finalist.
2. Collect `00_COMPARISON_MATRIX.md` and `00_MERGE_RECOMMENDATION.md` plus full package.
3. Score finalists with same rubric.
4. Run final compare and choose winner plan.

## 7) Post-round checklist
- Archive raw submissions with timestamp.
- Save score sheets.
- Record winner rationale and selected imports.
- Mark blocked decisions for implementation phase.

## 8) Common failure modes
- Missing package files.
- No evidence for major claims.
- Constraint violations (memory isolation, approval boundaries).
- Resource model missing quantification.

## 9) Decision output after tournament
Produce:
- final chosen plan id
- required merges from other finalists
- first implementation wave ticket list
- risk watchlist and approval checkpoints
