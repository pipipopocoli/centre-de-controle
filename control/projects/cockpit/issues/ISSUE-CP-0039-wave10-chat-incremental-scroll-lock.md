# ISSUE-CP-0039 - Wave10 chat incremental scroll lock

- Owner: leo
- Phase: Implement
- Status: Done

## Objective
- Remove chat full refresh rebuild behavior.
- Keep scroll stable when new messages arrive.
- Keep chat readable with context chip and compact hierarchy.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/chatroom.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`

## Scope (Out)
- Runtime dispatch logic
- Tournament files

## Done (Definition)
- [x] Global and thread lists update incrementally (append-only when possible).
- [x] If user is scrolled up, viewport does not jump.
- [x] If user is at bottom, viewport sticks to bottom.
- [x] Context chip is visible and clearable in composer.
- [x] QA evidence includes normal and degraded screenshots (mapped to matrix).

## Verification
- Code implementation in `chatroom.py` verified using `scrollToBottom()` native semantics and deferred layout calculation updates (`QTimer.singleShot(0, ...)`).
- Visual validations mapped in `CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md` (UI-06, UI-07).

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
