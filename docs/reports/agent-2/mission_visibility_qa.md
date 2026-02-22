# QA: Active Mission Visibility

## Context
Code: `app/ui/agents_grid.py`
Style: `app/ui/styles.py` (`QLabel#agentTask`)

## Checklist
- [x] **Location**: Task text is below the status pill and above the progress bar? (Yes)
- [x] **Labeling**: Section header "ACTIONS EN COURS" is present? (Yes, `agentTaskHeader`)
- [ ] **Prominence**:
  - [ ] Font Weight: `WEIGHT_NORMAL`. Is it bold enough? -> *Recommendation: Consider SemiBold for active missions.*
  - [ ] Color: `TEXT_PRIMARY`. Is it distinct from the header? (Yes, Header is Tertiary/Gray).
- [ ] **Readability**:
  - [x] Line Height: 1.3 (Good).
  - [ ] Word Wrap: Enabled.
  - [ ] Truncation: **Missing**. Risk of card expansion.

## Visual Check
![Mission Visibility](./mission_visibility_check.png)

## Recommendations
1.  **Boost Weight**: Change `font-weight` to `WEIGHT_SEMIBOLD` for `QLabel#agentTask` to make the mission pop more.
2.  **Dynamic Color**: Consider using `ACCENT_PRIMARY` color for the mission text when status is 'Executing', to link it visually to the 'EN MISSION' pill.
