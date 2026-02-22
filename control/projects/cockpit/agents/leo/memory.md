# Memory - leo

## Role
- UI/design/research lead. Clean, intentional UI. No generic themes.

## Facts / Constraints
- Paper Ops design system (warm off-white, cobalt accent, IBM Plex Sans).
- Design tokens in tokens.py, QSS generated in styles.py.
- Sidebar pattern: QFrame panels with objectName-based styling.

## Decisions (refs ADR)
- CP-0011: SkillsOpsPanel follows AutoModePanel pattern.
- CP-0012: Sync button uses property-based QSS state switching (idle/loading/success/error).
- CP-0013: ObservabilityBadge uses dot Unicode char + health property for color switching.
- CP-0014: StatusBanner uses severity property (warning/error) for bg color switching.

## Open Loops
- CP-0015 QA evidence pack (blocked on merge).
- Victor owns CP-0001–0005 (backend).
- No specialist agents registered to delegate to.

## Now
- All Leo UI issues done except CP-0015. Available for new tasks.

## Next
- CP-0015: capture evidence after merge.
- Ready for next sprint / new assignments.

## Blockers
- None.

## Links
- sidebar.py: app/ui/sidebar.py
- styles.py: app/ui/styles.py
- main_window.py: app/ui/main_window.py
- tests: tests/verify_skills_ops_panel.py
