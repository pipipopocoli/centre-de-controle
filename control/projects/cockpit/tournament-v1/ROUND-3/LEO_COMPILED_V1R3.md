# Round 3 - Leo Compiled V1R3

## Context Lock
- PROJECT LOCK: cockpit
- Base docs:
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/LEO_BIBLE_OWNER_V1R1.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/VICTOR_ARCH_RISK_V1R1.md
  - /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-2/*

## Changelog Diff Vs R1
1. Added execution cap: first implementation wave limited to 12 P0/P1 items.
2. Added owner column and ETA requirement for all accepted proposals.
3. Added urgency ranking logic to workflow views.
4. Added reliability annex: retry budget, severity model, stale-state marker.
5. Added outlier intake rubric and integration cap (max 3 outlier ideas).
6. Added freeze rule on unresolved critical blockers.
7. Added action-first chapter headers and canonical-source tags.
8. Reduced visual ambition in V1 to protect delivery speed.
9. Integrated actual UI evidence (Skills Ops, Tournament V2) to prove feasibility and zero-cost delivery.

## Critique Integration Ledger

### From Agent-11 (Feasibility)
| Critique ID | Decision | Reason |
|---|---|---|
| A11-01 | accepted | aligns with anti-overengineering and immediate delivery |
| A11-02 | accepted | owner clarity mandatory for execution |
| A11-03 | accepted | gives anti-complexity enforcement |
| A11-04 | accepted | required for measurable readability goal |
| A11-05 | accepted | gate simplification preserves velocity |
| A11-06 | accepted | protects scope from outlier sprawl |
| A11-07 | accepted | removes source ambiguity |
| A11-08 | accepted | adds clear reject criterion |

### From Agent-12 (Reliability)
| Critique ID | Decision | Reason |
|---|---|---|
| A12-01 | accepted | retry budget needed for deterministic behavior |
| A12-02 | accepted | severity model improves operator response |
| A12-03 | accepted | blocker recovery must be explicit |
| A12-04 | deferred | compatibility window needed only if legacy clients confirmed |
| A12-05 | accepted | session backup is low-cost and high-value |
| A12-06 | accepted | warning without actions is weak UX |
| A12-07 | accepted | stale marker improves trust in status cards |
| A12-08 | accepted | postmortems improve learning loop |

### From Agent-13 (Operator Flow)
| Critique ID | Decision | Reason |
|---|---|---|
| A13-01 | accepted | urgency ranking resolves counter ambiguity |
| A13-02 | accepted | dual views reduce cognitive overload |
| A13-03 | accepted | ETA field improves predictability |
| A13-04 | accepted | escalation route matrix removes hesitation |
| A13-05 | accepted | waiting owner label is high clarity |
| A13-06 | accepted | daily digest keeps state fresh |
| A13-07 | accepted | conflict board needs deadlines |
| A13-08 | accepted | silent timeout closes blind spot |

### From Agent-14 (Annodine Simple)
| Critique ID | Decision | Reason |
|---|---|---|
| simple-6-chapter scope | accepted | good default for kickoff focus |
| simple-8-item execution set | accepted | maps cleanly to first lot creation |
| drop deep dashboards for now | accepted | preserves momentum |
| delay vector memory | accepted | not needed for immediate workflow fixes |
| keep one-week digest trial | accepted | fast feedback loop |
| strict 80/20 framing | accepted | matches V1 objective |

### From Agent-15 (Hors Norme)
| Critique ID | Decision | Reason |
|---|---|---|
| workflow control plane core idea | deferred | high leverage but too large for immediate V1 |
| event stream as source of truth | deferred | valuable for V2 architecture track |
| pilot status-transition event only | accepted | safe low-cost experiment |
| kill-switch thresholds | accepted | mandatory risk brake |
| deterministic replay ambition | deferred | requires deeper infra contract |
| preserve current file contracts | accepted | hard constraint for V1 |

## Compiled V1 Program Bible (Leo Angle)

### Priority Stack
- P0: Program Bible operating core + workflow status model.
- P1: Operator clarity and handoff precision.
- P2: Reliability guardrails and runtime contract checks.
- P3: outlier experiments only if no P0/P1 debt.

### Implementation Prep Set (12 Items Max)
1. Bible chapter skeleton (6 core chapters).
2. Canonical vocabulary dictionary.
3. Decision rights matrix L0/L1/L2.
4. Handoff packet template with ETA and DoD.
5. Status V4 mapping with waiting owner labels.
6. 60-second readability test protocol.
7. Urgency ranking rule and top-3 view.
8. Blocker taxonomy + escalation matrix.
9. Reliability annex (retry budget + severity model).
10. Mismatch banner action steps.
11. Daily digest template and cadence.
12. Gate checklist with freeze/veto logic.

### Zero-Cost Wins (Already Implemented)
- **Observability Panel (Skills Ops)**:
  -   Fully implemented `SkillsOpsPanel` with Sync/Memory badges (CP-0013).
  -   Status: Verified (23/23 tests pass).
  -   Cost: 0 (Done).
-   **Tournament Engine V2 (SFII)**:
  -   Visual bracket with Street Fighter II theme + strict logic (CP-Tournament).
  -   Status: Verified (Visual + Functional).
  -   Cost: 0 (Done).

### Acceptance Standards
- Each accepted item has owner, expected output path, and verifiable DoD.
- Any item without test method cannot enter implementation queue.
- If active planning WIP > 5, freeze new additions.

## Risks Still Open
- Compatibility window need is unknown until legacy usage is confirmed.
- Outlier pilot may distract if started too early.
- Documentation freshness depends on strict cadence discipline.

## Now / Next / Blockers
- Now: compiled UX-first V1 with feasibility and reliability corrections.
- Next: run scorecard against Victor compile and lock winner.
- Blockers: none.
