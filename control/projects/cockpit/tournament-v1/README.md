# Tournament V1 - Leo First Program Bible

## Purpose
- Build one official V1 program from Leo source plan first.
- Run a 3-round idea tournament to raise quality before any code implementation.
- Produce one final review packet for operator validation.

## Canonical Source
- Source plan: `/Users/oliviercloutier/Desktop/Cockpit/docs/cockpit_v2_project_spec.md`
- Project context lock: `cockpit`
- Output root: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`

## Rules
- All outputs are markdown files.
- All outputs are decision-complete and implementation-ready.
- No API/code change in this tournament phase.
- ASCII only style.
- WIP cap for writing streams: 5 active docs at once.

## Roles And Platforms
- `@leo` -> AG lane. Focus: UX, workflow clarity, program bible quality.
- `@victor` -> CDX lane. Focus: architecture, risks, execution sequence.
- `@agent-11` -> CDX. Feasibility and simplification critique.
- `@agent-12` -> AG. Reliability and resilience critique.
- `@agent-13` -> CDX. Operator workflow critique.
- `@agent-14` -> AG. Annodine/simple alternative (80/20 value).
- `@agent-15` -> CDX. Outlier/high-leverage alternative.

## Round Model
1. Round 0
- Extract and normalize V1 baseline from Leo source.
- Rebase roadmap and state to V1-first.
- Gate 0: no contradiction, each baseline chapter has objective + DoD + risks + tests.

2. Round 1
- `@leo` and `@victor` publish independent deep upgrades.
- Gate 1: each lead doc has >=20 qualified change proposals.

3. Round 2
- `@agent-11..@agent-15` publish critiques and alternatives.
- Gate 2: >=60 percent of critique items are directly actionable with verifiable DoD.

4. Round 3
- `@leo` and `@victor` compile, integrate, and justify accept/reject/defer on all critiques.
- Gate 3: both compiled docs pass weighted scorecard without critical risk veto.

5. Final
- Clems compares both compiled versions deeply.
- Clems publishes winner recommendation + fallback options.

## Weighted Scorecard
- Product impact: 30
- Operator and agent workflow fluidity: 25
- Feasibility for V1 implementation: 20
- Technical and process risk reduction: 15
- Delivery cost and timeline: 10
- Winner rule: highest total score, unless critical unresolved risk triggers veto.

## Deliverable Map
- `ROUND-0/00_V1_BASELINE_FROM_LEO.md`
- `ROUND-0/01_ROADMAP_V1_REBASE.md`
- `ROUND-0/02_STATE_V1_REBASE.md`
- `ROUND-1/LEO_BIBLE_OWNER_V1R1.md`
- `ROUND-1/VICTOR_ARCH_RISK_V1R1.md`
- `ROUND-2/AGENT-11_CRITIQUE_FEASIBILITY.md`
- `ROUND-2/AGENT-12_CRITIQUE_RELIABILITY.md`
- `ROUND-2/AGENT-13_CRITIQUE_OPERATOR_FLOW.md`
- `ROUND-2/AGENT-14_ALT_ANNODINE_SIMPLE.md`
- `ROUND-2/AGENT-15_ALT_HORS_NORME.md`
- `ROUND-3/LEO_COMPILED_V1R3.md`
- `ROUND-3/VICTOR_COMPILED_V1R3.md`
- `FINAL/00_SCORECARD_PONDEREE.md`
- `FINAL/01_CLEMS_DEEP_COMPARE.md`
- `FINAL/02_USER_REVIEW_PACKET.md`

## Validation Checklist
- Every file exists and is non-empty.
- Every proposal has problem, proposal, impact, risk, test, DoD.
- Round 3 docs include explicit accept/reject/defer mapping for all 5 critiques.
- Final scorecard is traceable and reproducible.
