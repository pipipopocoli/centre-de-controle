# V3.7 UI Spec (Leo)

Date: 2026-02-13
Project lock: cockpit

## UX intent
- Operator must understand in one glance:
  - who leads and who executes,
  - what each agent is doing now,
  - whether status is stale.

## UI decisions
- Keep chat rendering stable (QListWidgetItem text only).
- Do not reintroduce setItemWidget path.
- Group agent cards by hierarchy:
  - L0 - Orchestration
  - L1 - Leads
  - L2 - Specialists
- Make mission line more prominent:
  - label "Mission"
  - semibold when active status.
- Keep "Last update" stale state visible and red when stale.

## Microcopy lock
- Status labels:
  - En attente
  - Planifie
  - En cours
  - Ping envoye
  - Repondu
  - Verification
  - Bloque
  - Erreur
  - Termine

## QA checklist
- Cards render correctly with 1, 3, and 10 agents.
- No clipping on mission text.
- Timeline active phase still highlights correctly.
- Chat remains readable during refresh loop.

## Evidence targets
- docs/screenshots/v3.7/ui_before.png
- docs/screenshots/v3.7/ui_after_mock.png
- docs/reports/v3.7/ui_checklist.md
