# CP01 Vulgarisation Upgrade Wave07

## Scope and intent
- Owner: @nova
- Goal: improve service-side code quality and operator clarity for Vulgarisation.
- In scope:
  - `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_accessibility.py`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_comprehension.py`
- Explicit no-overlap with Leo UI lane: no edits in `app/ui/project_pilotage.py`, `app/ui/project_timeline.py`, `app/ui/theme.qss`.
- No tournament paths touched.

## What changed
- Deterministic Brief 60s fallback logic was added in `project_bible.py`.
  - Added sanitizers for empty/placeholder values.
  - Added explicit resolvers for rows:
    - `On est ou`
    - `On va ou`
    - `Pourquoi`
    - `Comment`
  - Rows are now guaranteed non-empty even when source sections are partial.
- Timeline rendering semantics were upgraded in `project_bible.py`.
  - Added deterministic event summary normalization helper.
  - Event text is now action-first, concise, and clamped.
  - Lane and severity are explicit in event text (not color-only), for example:
    - `[lane=runtime severity=warn] Review KPI snapshot | close_rate_24h=...`
- Added delta signal since last refresh in snapshot + HTML.
  - New snapshot block: `delta_since_last_refresh`.
  - Tracks status in `{initial, changed, unchanged}` with hash/timestamp context.
  - Exposed in header meta and in Brief section row `Delta refresh`.
- Offline contract preserved.
  - File links remain `file://` when files exist.
  - No new external dependency.
  - Existing evidence link behavior unchanged.
- Tests were extended for the new behavior.
  - Added fallback and delta lifecycle checks in `verify_project_bible.py`.
  - Added contract checks for `delta_since_last_refresh` in `verify_vulgarisation_contract.py`.
  - Added accessibility checks for lane/severity markers in timeline event text.
  - Added lightweight rendered HTML assertions in comprehension test.

## Why this improves operator comprehension
- Brief rows no longer collapse to `n/a` under partial inputs, so the operator always gets a usable 60s summary.
- Timeline event text is action-first, so operator scanning is faster under pressure.
- Lane + severity in plain text remove color-only dependence and improve accessibility.
- Delta signal makes refresh impact explicit, reducing guesswork between two reads.

## Before and after behavior examples
- Brief 60s fallback:
  - Before: `On est ou` or `Pourquoi` could become empty/weak under sparse STATE/ROADMAP sections.
  - After: deterministic fallback rows are always non-empty and stable.
- Timeline event readability:
  - Before: Event column used raw title only.
  - After: Event column uses normalized summary with explicit context:
    - `[lane=delivery severity=info] Review update: STATE updated`
- Refresh delta visibility:
  - Before: no direct hint if data changed since last refresh.
  - After: compact delta hint in header and Brief row, for example:
    - `changed: Delta detected 8f1a22b4 -> 1c09dd6a since 2026-02-19T17:52:01+00:00.`

## Test run outputs
- Command:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_project_bible.py`
  - Output:
    - `OK: vulgarisation html generation`
    - `OK: monthly estimator source order verified`
    - `OK: vulgarisation widget rendering`
    - `OK: vulgarisation verified`
- Command:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_contract.py`
  - Output:
    - `OK: vulgarisation contract verified`
- Command:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_accessibility.py`
  - Output:
    - `OK: vulgarisation accessibility verified`
- Command:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_comprehension.py`
  - Output:
    - `OK: comprehension gate verified | answer_accuracy=0.950 scenario_pass_rate=1.000`

## Operational cadence note
- 2h reporting is manual in this delivery.
- Nova posts `Now / Next / Blockers` in global chat with tags `status`, `report`, `creative-science`.

## Wave08 advisory lock
- Brief 60s contract: locked.
  - deterministic fallback remains active for `On est ou`, `On va ou`, `Pourquoi`, `Comment`.
- Recommendation ledger contract: locked.
  - each recommendation includes `owner`, `next action`, and `evidence path`.

### Ledger snapshot (operator lock)
- Accepted:
  - `R1` template brief unique par checkpoint.
  - `R3` mapping risque -> preuve testable.
- Pending:
  - `R2` confidence gate for SLO sample volume.
  - `R4` owner ack SLA <= 2h.
  - `R5` lane-level traceability for each recommendation.
- Rejected:
  - none (this cycle).
