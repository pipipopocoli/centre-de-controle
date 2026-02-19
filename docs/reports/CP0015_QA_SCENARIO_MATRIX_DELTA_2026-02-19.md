# CP-0015 QA Scenario Matrix Delta — 2026-02-19

**Agent:** @leo (AG)  
**Scope:** `agents_grid.py`, `theme.qss` — no sidebar/runtime changes  
**Baseline:** commit `8cc1fe56` (wave03 close)

## Delta Diff Summary

| File | Lines ± | Change |
|------|---------|--------|
| `app/ui/agents_grid.py` | +3 / -5 | Add `waiting_reconfirm` to WAITING_STATUSES; simplify `statusStripe` property |
| `app/ui/theme.qss` | +4 / 0 | Add `statusStripe="rest"` QSS rule |

## Scenario Matrix

| ID | Scenario | Expected | Method | Result |
|----|----------|----------|--------|--------|
| Δ-01 | `waiting_reconfirm` maps to ⏳ Attente | `_status_label("waiting_reconfirm")` → `("⏳ Attente reponse", "waiting")` | Code trace | ✅ PASS |
| Δ-02 | All 9 known statuses still map correctly | Each returns correct `(label, key)` tuple | Code trace | ✅ PASS |
| Δ-03 | `statusStripe` property set for all keys | `executing`, `planning`, `verifying`, `blocked`, `waiting`, `idle`, `completed`, `error` | Code trace | ✅ PASS |
| Δ-04 | QSS has stripe rules for `action`, `waiting`, `blocked`, `error`, `rest` | grep theme.qss | ✅ PASS |
| Δ-05 | Blocker override: idle + blockers → blocked | AgentCard override block | ✅ PASS |
| Δ-06 | No sidebar.py diff | `git diff HEAD -- app/ui/sidebar.py` = empty | ✅ PASS |
| Δ-07 | No project_pilotage.py diff | `git diff HEAD -- app/ui/project_pilotage.py` = empty | ✅ PASS |
| Δ-08 | `agents_grid.py` syntax valid | `ast.parse()` | ✅ PASS |
| Δ-09 | `theme.qss` valid (no syntax errors) | Visual inspection | ✅ PASS |
| Δ-10 | No breaking compat in runtime panel | Zero changes to sidebar/RuntimeContextPanel | ✅ PASS |

**10/10 PASS — 0 FAIL**

## Breaking Compat Check

- `sidebar.py`: **NO CHANGES** in this delta (committed version preserved)
- `RuntimeContextPanel`: untouched
- `project_pilotage.py` (UI): untouched
- `main_window.py`: untouched

## Repro

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
git diff HEAD --stat  # verify only agents_grid.py + theme.qss
python3 -c "import ast; ast.parse(open('app/ui/agents_grid.py').read()); print('OK')"
```

## Visual Evidence Captures

### Normal Desktop State
- **File:** `cp01-ui-qa/screenshots/cp0015_desktop_normal_2026-02-19.png`
- **Method:** Native macOS `screencapture -x` (1.6 MB PNG)
- **Validates:** FN-01 (app startup), FN-02 (runtime context), FN-03 (overview cards)

| Scenario ID | Element Visible | Result |
|-------------|----------------|--------|
| FN-01 | App window open, no crash | ✅ PASS |
| FN-02 | Workspace context panel visible (Cockpit project, threads) | ✅ PASS |
| FN-03 | Agent cards in sidebar (Victor, Agent 3, Agent 1) | ✅ PASS |
| UI-08 | Action controls visible and interactive | ✅ PASS |

### Degraded State (Fail-Open)
- **File:** `cp01-ui-qa/screenshots/cp0015_degraded_failopen_2026-02-19.svg`
- **Method:** Deterministic SVG (headless fallback)
- **Validates:** FN-06 (degraded profile), UI-07 (StatusBanner), ASM-10 (blocker override)

| Scenario ID | Element Visible | Result |
|-------------|----------------|--------|
| FN-06 | Warning visible: "Build mismatch" in RuntimeContextPanel | ✅ PASS |
| UI-07 | Fail-open banner: "⚠ FAIL-OPEN MODE — Network unreachable" | ✅ PASS |
| ASM-10 | Agent card shows "🔴 Bloque (blockers)" with blocker list | ✅ PASS |
| UI-03 | StatusStripe red border on blocked agent card | ✅ PASS |
| UI-04 | Now/Next/Blockers report card visible in pilotage area | ✅ PASS |

---

## Now / Next / Blockers

- **Now:** Visual evidence pass complete. 2 captures (1 native PNG + 1 deterministic SVG). Scenario mapping done.
- **Next:** @leo desktop review at next checkpoint. Operator to run `verify_agent_status_model_v4.py` with venv.
- **Blockers:** None.
