# Issue: Integrate HTML Docs (Roadmap & Tournament) into Cockpit UI

**ID:** ISSUE-CP-0015
**Type:** Feature / UI
**Status:** Deferred
**Priority:** High
**Assignee:** Clems (Orchestrator) -> Léo (UI Lead)

- Phase: Backlog
- Status: Deferred
- Decision note: Backlog deferred, non-bloquant pour Wave08 closeout.

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
- [ ] Create `ISSUE-CP-0015` file.
- [ ] Update `roadmap` in `project.json` / `settings.json`.
- [ ] Assign to Léo for implementation.
- [ ] Implement `WebDocViewer` widget.
- [ ] Add sidebar entry.

## Deferral policy
- This issue remains valid but is explicitly deferred.
- It is not a release blocker for Wave08 closeout.
- Re-open when UI docs embedding becomes active scope.

## Acceptance Criteria
- [ ] User can click a "Roadmap" icon in the app.
- [ ] `cockpit_v2_roadmap.html` renders correctly inside the app window.
- [ ] User can switch to "Tournament" view.
- [ ] `TOURNAMENT_ARENA.html` renders correctly with its animations.
