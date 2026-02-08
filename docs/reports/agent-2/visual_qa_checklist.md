# Visual QA: Agent Cards

## Checklist
- [x] **Layout & Spacing**: Padding 12px everywhere? Spacing 8px vertical?
- [x] **Status Pills**: 
  - [x] 'Executing' -> Blue Pulse (Correct)
  - [x] 'Planning' -> Amber (Correct)
  - [x] 'Blocked' -> Red/Black (Correct)
- [ ] **Heartbeat / Stale State**: 
  - [ ] Code sets `setProperty("stale", ...)` but **QSS is missing stylistic response**. (Current: No visual difference).
- [ ] **Long Task Text**:
  - [x] `setWordWrap(True)` is present.
  - [ ] **Risk**: No `maxHeight` or `elideMode` set. A very long task description could expand the card indefinitely, breaking the grid row alignment.
- [x] **Typography**:
  - Task Header: Uppercase, 9px, Tertiary (Clear).
  - Status: 10px, Bold (Readable).

## Visual Evidence

### 1. Active State (Ideal)
*Mockup of an agent in 'Executing' state.*

![Active Agent Card](./agent_card_active.png)

### 2. Blocked/Stale State (Edge Case)
*Mockup of an agent 'Blocked' with a stale heartbeat.*

![Blocked Agent Card](./agent_card_blocked.png)

## Recommendations
1.  **Add Stale Style**: Add `QLabel#agentSignal[stale="true"] { color: #EF4444; font-weight: bold; }` to `styles.py`.
2.  **Clamp Task Text**: Set a maximum height or character limit for the task description to ensure uniform card heights.
