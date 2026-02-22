# ISSUE-CP-0041 - Wave10 UI click context routing

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Bind UI selection to outgoing chat and mention-driven run requests.
- Ensure context is explicit, optional, and traceable.

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/agents_grid.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/chatroom.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/data/store.py`

## Scope (Out)
- Tournament files
- Provider routing changes

## Context contract
```json
{
  "kind": "agent|timeline|issue|state_item",
  "id": "string",
  "title": "string",
  "source_path": "abs path or ''",
  "source_uri": "file://... or ''",
  "selected_at": "ISO-8601"
}
```

## Done (Definition)
- [x] Agent card click attaches `context_ref`.
- [x] Timeline row selection attaches `context_ref`.
- [x] Pilotage state list selection attaches `context_ref`.
- [x] `record_mentions` persists `context_ref` in requests payload.
- [x] Missing context remains valid and non-breaking.

## Verification
- Manual: click item -> send message -> verify payload has `context_ref`.
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_timeline_feed.py`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/requests.ndjson`

## Closeout
- Closed at (UTC): `2026-02-22T18:13:56Z`

## Evidence
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave10_runtime_lane.py` -> `OK: wave10 runtime/backend lane verified` (includes `cp-0041` pass)
- `/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_timeline_feed.py` -> `OK: timeline feed contract + determinism verified`
- Context payload lock checked in `verify_wave10_runtime_lane.py`: top-level `context_ref` and `message.context_ref` persisted in `requests.ndjson`
