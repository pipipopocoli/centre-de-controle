# CP-0037 QA Scenario Matrix — 2026-02-21

**Agent:** @agent-6
**Scope:** `project_pilotage.py`, `project_timeline.py`, `theme.qss`
**Objective:** Finalize scenario matrix for dual-root control badges (repo/app) and UI modes (Simple/Tech).

## Scenario Matrix

| ID | Scenario | Expected | Method | Result |
|----|----------|----------|--------|--------|
| CP37-01 | Pilotage Simple Mode (Healthy) | Core repo/app health clearly visible without deep technical clutter. | `verify_ui_polish.py` | ✅ PASS |
| CP37-02 | Pilotage Tech Mode (Healthy) | Both `gateBadgeRepo` and `gateBadgeApp` show `Healthy` (Green) with full diagnostic depth. | `verify_ui_polish.py` | ✅ PASS |
| CP37-03 | Pilotage Repo Badge Degraded | `gateBadgeRepo` shows `Degraded` (Red/Pink) with precise error in Tech mode. | Mocked/Subprocess | ✅ PASS |
| CP37-04 | Pilotage App Badge Degraded | `gateBadgeApp` shows `Degraded` (Red/Pink) with precise error in Tech mode. | Mocked/Subprocess | ✅ PASS |
| CP37-05 | Timeline Hybrid Feed (Tech) | Timeline renders control events distinctly. | `verify_hybrid_timeline.py` | ✅ PASS |

**5/5 PASS — 0 FAIL**

## Repro Steps

To reproduce the programmatic UI checks for Simple and Tech modes:
```bash
# Provide virtual environment Python path if necessary
.venv/bin/python scripts/verify_ui_polish.py
.venv/bin/python tests/verify_hybrid_timeline.py
```

**Expected behavior:**
- `verify_ui_polish.py` captures `pilotage_simple_mode.png` and `pilotage_tech_mode.png` into `docs/reports/cp01-ui-qa/evidence/`.
- `verify_hybrid_timeline.py` outputs structural PASS for `HT-*` scenarios.

## Visual Evidence Captures

Screenshot mapping is detailed in related evidence files (e.g., CP0015 UI Delta). Core artifacts include:
- `docs/reports/cp01-ui-qa/evidence/pilotage_simple_mode.png`
- `docs/reports/cp01-ui-qa/evidence/pilotage_tech_mode.png`
- *(Degraded mock captures as specified in CP0015 delta)*

---

## Now / Next / Blockers

- **Now:** Finalized the CP-0037 scenario matrix covering Simple/Tech modes, repo/app boundaries, and degraded states.
- **Next:** Hand over to @agent-7 for screenshot mapping and final evidence packet compilation.
- **Blockers:** None.
