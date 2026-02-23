# ISSUE-CP-0046 - Wave13 Live View Task+Code Hybrid

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
Add a compact live view in Pilotage with code/task/agent lanes.

## Scope (In)
- `app/services/live_activity_feed.py`
- `app/ui/project_pilotage.py`

## Done (Definition)
- [x] Service `build_live_activity_feed(project, limit)` implemented.
- [x] Repo source resolution: linked repo first, workspace fallback.
- [x] Pilotage shows `Code now`, `Tasks now`, `Agents now`.
- [x] Git lane cached at 15s, runtime/task lane refreshed at 5s.

## Closeout
- Closed at: 2026-02-23T07:24Z
- Proof pack:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0046_CP0047_PROOF_2026-02-23T0724Z.md`
- Live linked-repo evidence:
  - `project_id=motherload`
  - `repo_source=linked_repo`
  - `repo_path=/Users/oliviercloutier/Desktop/motherload_projet`
  - `pilotage_live_repo_path=/Users/oliviercloutier/Desktop/motherload_projet`
- Test/QA:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_live_activity_feed.py`

## Notes
- Offline/local only.
