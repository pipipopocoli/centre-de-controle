# IMPLEMENATION PROPOSAL - VORTEX UI (FINAL)

## 1. Objective
Develop "Vortex": A high-performance, event-driven UI layer for Cockpit, hardened by strict automated compliance gates to ensure "Zero Search / Zero Lag" reliability.

## 2. Scope in/out
**In:**
- **Product:** Real-time websocket event bus (`VortexEngine`).
- **Process:** Automated shell-based QA gates for submission validity.
- **UI:** "Heads-up" overlay for immediate blocker visibility.
- **Input:** Keyboard-centric navigation (VIM style).

**Out:**
- Legacy polling mechanisms.
- Heavy historical analytics.
- **Premature Optimization:** 60 FPS hard target (relaxed to "Fluid" definition).

## 3. Architecture/workflow summary
- **Core:** `VortexEngine` (PySide6 + asyncqt) managing a dedicated event loop.
- **Validation:** `ComplianceShell` scripts running `rg` and `test` validations pre-commit.
- **Data:** In-memory `StateCache` subscribing to `journal.ndjson` tail streams.

## 4. Changelog vs previous version
- **Absorbed:** Integration of Agent 11's deterministic QA gates.
- **Refined:** Shifted focus from raw FPS to structural integrity.
- **Extended:** Added `ComplianceShell` architecture component.

## 5. Imported opponent ideas (accepted/rejected/deferred)
- **Accepted (Agent 11):** Automating existence checks via `test -f`. *Reason: Ensures zero-search determinism.*
- **Accepted (Agent 11):** Regex-based header validation (`rg -n "^## ..."`). *Reason: Enforces structural compliance.*
- **Accepted (Agent 11):** Explicit Blocker Declaration format. *Reason: Improves async communication clarity.*

## 6. Risk register
- **Risk:** Async loop locking GUI thread. **Mitigation:** Thread separation.
- **Risk:** Over-engineering compliance gates. **Mitigation:** Limit to file/header checks only.

## 7. Test and QA gates
- **Product Gate:** `verify_vortex_event_loop.py` must pass.
- **Compliance Gate 1:** `test -f .../agent-6_SUBMISSION_V1_FINAL.md`
- **Compliance Gate 2:** `rg -n "^## [1-9]\\." .../agent-6_SUBMISSION_V1_FINAL.md`
- **Visual:** Snapshot comparison for "Heads-up" mode.

## 8. DoD checklist
- [ ] `VortexEngine` class implemented.
- [ ] `ComplianceShell` script valid.
- [ ] Tests passed.
- [ ] Blocker declaration format verified.

## 9. Next round strategy
- Operationalize `ComplianceShell` for all future Wave 2 UI tasks.
- Benchmarking `VortexEngine` against legacy `SidebarWidget`.

## 10. Now/Next/Blockers
- **Now:** Submitted Final V1.
- **Next:** Await Operator Review / Tournament Result.
- **Blockers:** None.
