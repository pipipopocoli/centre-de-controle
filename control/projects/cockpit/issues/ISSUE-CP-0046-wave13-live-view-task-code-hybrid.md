# ISSUE-CP-0046 - Wave13 Live View Task+Code Hybrid

- Owner: victor
- Phase: Implement
- Status: Open

## Objective
Add a compact live view in Pilotage with code/task/agent lanes.

## Scope (In)
- `app/services/live_activity_feed.py`
- `app/ui/project_pilotage.py`

## Done (Definition)
- [ ] Service `build_live_activity_feed(project, limit)` implemented.
- [ ] Repo source resolution: linked repo first, workspace fallback.
- [ ] Pilotage shows `Code now`, `Tasks now`, `Agents now`.
- [ ] Git lane cached at 15s, runtime/task lane refreshed at 5s.

## Notes
- Offline/local only.
