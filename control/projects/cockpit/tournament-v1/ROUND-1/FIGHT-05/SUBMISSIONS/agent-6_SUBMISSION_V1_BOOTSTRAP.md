# IMPLEMENATION PROPOSAL - VORTEX UI

## 1. Objective
Develop "Vortex": A high-performance, event-driven UI layer for Cockpit that minimizes latency and maximizes agent observability through a "Zero Search / Zero Lag" paradigm.

## 2. Scope in/out
**In:**
- Real-time websocket event bus for UI updates.
- 60 FPS rendering target for agent status grids.
- "Heads-up" overlay for immediate blocker visibility.
- Keyboard-centric navigation (VIM style).

**Out:**
- Legacy polling mechanisms.
- Heavy historical analytics (delegated to offline reporting).
- Mobile support (focus on desktop command center).

## 3. Architecture/workflow summary
- **Core:** `VortexEngine` (PySide6 + asyncqt) managing a dedicated event loop.
- **Data:** In-memory `StateCache` subscribing to `journal.ndjson` tail streams.
- **View:** `QGraphicsScene` for agent nodes to offload rendering from main widget tree.

## 4. Changelog vs previous version
- **New:** Introduced `VortexEngine` loop.
- **Changed:** Deprecated `QTimer` polling in favor of `QFileSystemWatcher` + signal streamline.
- **Removed:** Redundant "loading" states (optimistic UI).

## 5. Imported opponent ideas (accepted/rejected/deferred)
- (Phase A: None - Bootstrap)

## 6. Risk register
- **Risk:** Async loop locking GUI thread. **Mitigation:** Thread separation for IO.
- **Risk:** High memory usage with `QGraphicsScene`. **Mitigation:** Viewport culling.

## 7. Test and QA gates
- **Perf:** Frame time < 16ms under load (50 active agents).
- **Correctness:** `verify_vortex_event_loop.py` must pass.
- **Visual:** Snapshot comparison for "Heads-up" mode.

## 8. DoD checklist
- [ ] `VortexEngine` class implemented.
- [ ] Websocket/Signal bridge established.
- [ ] 60 FPS target met in benchmark.
- [ ] Tests passed.

## 9. Next round strategy
- Analyze Agent 11's bootstrap for integration opportunities.
- Refine `StateCache` based on opponent's data model.

## 10. Now/Next/Blockers
- **Now:** Submitted Bootstrap V1.
- **Next:** Read Agent 11 Bootstrap.
- **Blockers:** None.
