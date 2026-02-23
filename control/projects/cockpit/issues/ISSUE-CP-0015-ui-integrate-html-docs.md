# Issue: Integrate HTML Docs (Roadmap & Tournament) into Cockpit UI

**ID:** ISSUE-CP-0015
**Type:** Feature / UI
**Status:** Done
**Priority:** High
**Assignee:** Clems (Orchestrator) -> Léo (UI Lead)

- Phase: Ship
- Status: Done
- Decision note: Reactivated and completed in Wave13 closeout lane.

## Context
We have generated high-value HTML documentation files:
1. `docs/cockpit_v2_roadmap.html` (Visual Gantt & Strategy)
2. `control/projects/cockpit/tournament-v1/TOURNAMENT_ARENA.html` (Battle Royal Bracket)

Currently, the user has to leave the app and open these in a browser. They requested: *"est-ce que dans mon application je pourrais voir les htlm?"* and *"envoie la demande a clem pour appliquer ça"*.

## Objective
Embed a `QWebEngineView` (or similar web viewer) within the Cockpit application to allow seamless viewing of these local HTML artifacts without context switching.

## Proposed Solution (UI)
- Add a new "Docs" or "Roadmap" tab/icon in the Sidebar.
- Create a `DocViewer` component in `app/ui/` that wraps `QWebEngineView`.
- Create a simple navigation selector (Roadmap vs Tournament).
- Load local file paths securely.

## Tasks
- [x] Create `ISSUE-CP-0015` file.
- [x] Update `roadmap` in `project.json` / `settings.json`.
- [x] Assign to Léo for implementation.
- [x] Implement `WebDocViewer` widget.
- [x] Add sidebar entry.

## Delivery notes
- Docs tab added in app center tabs.
- Sidebar Docs button routes directly to Docs tab.
- Doc viewer supports Roadmap and Tournament local HTML.
- Runtime fallback is explicit read-only when WebEngine is unavailable.

## Acceptance Criteria
- [x] User can click a "Roadmap" icon in the app.
- [x] `cockpit_v2_roadmap.html` renders correctly inside the app window.
- [x] User can switch to "Tournament" view.
- [x] `TOURNAMENT_ARENA.html` renders correctly with its animations.

## Closeout
- Closed at: 2026-02-23T09:09Z
- Evidence packet:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0015_CP0042_CLOSEOUT_2026-02-23T0909Z.md`
- Source files:
  - `/Users/oliviercloutier/Desktop/Cockpit/app/ui/doc_viewer.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/app/ui/sidebar.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`
- Verification:
  - `QT_QPA_PLATFORM=offscreen ./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_doc_viewer.py`
