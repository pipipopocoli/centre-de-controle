# ISSUE-0006 - UI redesign V1 (research first)

- Owner: leo (@leo)
- Phase: Plan
- Status: Todo

## Objective
- Upgrade Cockpit UI from "functional but ugly" to a high-quality, intentional "mission control" experience.

## Scope (In)
- Phase 1 (Research + Spec):
  - Propose 2-3 visual directions (type, color palette, layout, motion).
  - Pick 1 recommendation with rationale + quality checklist.
  - Define constraints (desktop + mobile, contrast, performance).
- Phase 2 (Implementation):
  - Centralize styling (QSS / styles module).
  - Refactor core screens (Sidebar, Agents grid/cards, Roadmap, Chat) to match chosen direction.
  - Add a screenshot in `docs/` for review.

## Scope (Out)
- "Big redesign" without research.
- Uncontrolled theme churn (no random restyling every week).
- Anything that breaks core interactions (project switch, chat, agent cards).

## Now
- None.

## Next
- Research deliverable:
  - 2-3 directions + a recommendation.
  - Concrete typography choice (not a default stack) and spacing scale.
  - Color system (backgrounds, surfaces, text, accents) + contrast notes.
  - A short "Do / Don't" list to avoid generic UI patterns.

## Blockers
- None.

## Done (Definition)
- Phase 1 done:
  - 2-3 directions documented + 1 recommended direction.
  - Checklist + acceptance criteria for implementation.
- Phase 2 done:
  - UI is readable, consistent, and intentional.
  - Manual QA: resize works, no clipped text, contrast is reasonable.
  - Screenshot committed for review.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- QSS limitations may constrain fancy ideas (keep it pragmatic).
- Visual changes can hide regressions (needs a tight manual QA checklist).
