# Cockpit UI Lock Feature Report (Now/Next/Blockers)

## Objective
To remove operator confusion regarding project identity and runtime truth, by adding an explicit visual lock for the canonical `cockpit` project and a warning for mis-matched/archived selections.

## Implementation Details

1. **`app/ui/sidebar.py`**:
   - Modified `RuntimeContextPanel` to add a new `QLabel` designated as `self.project_warning`.
   - Updated the `set_context` method to check if the `project_value` is `"cockpit"`.
   - If canonical (`"cockpit"`): Prepends "🔒 " to the project name, appends `(Canonical)`, and updates a custom QObject property `canonical="true"`. The warning label is hidden.
   - If non-canonical (e.g., archived project): Prepends "⚠️ " to the project title, appends `(Non-canonical)`, sets `canonical="false"`, and shows the warning label with red text explaining the mismatch.

2. **`app/ui/theme.qss`**:
   - Added styles for `QLabel#runtimeContextTitle[canonical="true"]` to appear in green (`#166534`).
   - Added styles for `QLabel#runtimeContextTitle[canonical="false"]` to appear in red (`#B91C1C`).
   - Added `QLabel#projectMismatch` styling (red text, red background, border) to immediately draw attention.

## Verification
- Code review performed to ensure zero impact on existing refresh/chat/pilotage signals; changes are purely cosmetic in `RuntimeContextPanel.set_context()`.

## Now / Next / Blockers

### Now
- Merged visual lock logic indicating the canonical `cockpit` project with a green lock.
- Added red mismatch warning for archived projects in the sidebar context panel.
- Handled UI updates gracefully using `style().polish()` to re-evaluate the custom property without requiring a full app restart.

### Next
- Operator to test these visual cues on their local machine.
- Verify whether the timeline/roadmap UI needs similar canonical checks scattered throughout.

### Blockers
- **Screenshot Evidence Missing**: Visual verification through automated screenshots was blocked because PySide6 could not be located or installed via `pip` due to system permission constraints inside the runtime environment (`[Errno 1] Operation not permitted: '/Users/oliviercloutier/Library/Python/3.11'`). Operator is advised to load the app to verify visually.
