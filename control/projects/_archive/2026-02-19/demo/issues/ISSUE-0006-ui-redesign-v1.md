# ISSUE-0006 - UI redesign V1 (research first)

- Owner: leo (@leo)
- Phase: Ship
- Status: Done

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
- Phase 2 implementation completed (Paper Ops in QSS).
- Chat action buttons compact + tooltips.
- Screenshot added for review.

## Next
- Phase 3 release checklist + monitoring.

## Research Summary (Phase 1 Done)
- Direction A: Paper Ops (recommended)
  - Warm off-white background, crisp borders, cobalt accent.
  - IBM Plex Sans + Plex Mono.
- Direction B: Signal Grid
  - Industrial mission-control, high-contrast panels, orange/teal accents.
- Direction C: Orbit Minimal
  - Cool gradients, soft glass surfaces, minimal chrome.

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
- UI research: docs/ui-research.md
- PR: https://github.com/pipipopocoli/centre-de-controle/pull/6

## Risks
- QSS limitations may constrain fancy ideas (keep it pragmatic).
- Visual changes can hide regressions (needs a tight manual QA checklist).
