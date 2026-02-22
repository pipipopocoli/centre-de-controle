# Zero Search Rules (Dual Stage, Anti-Lag)

Hard constraints
1. Read only files explicitly listed in your prompt/README.
2. Write only output paths explicitly listed in your prompt/README.
3. Do not use project-wide search.
4. Do not inspect unrelated folders.
5. If a required file is missing, stop and report blocker.

Read policy for L3+
- Allowed:
  - locked historical project files explicitly listed in README,
  - your own prior submissions,
  - your current opponent files explicitly listed.
- Forbidden:
  - in-progress submissions from other active L3 competitors,
  - unrelated fight folders,
  - broad repo scans.

Output lock
- For future rounds, active dispatch requires two outputs:
  - `*_FINAL.md`
  - `<agent_id>_FINAL_HTML/index.html`
- `*_BOOTSTRAP.md` is not accepted for active dispatch.

Minimum required sections in FINAL submission
1. Objective
2. Scope in/out
3. Architecture/workflow summary
4. Changelog vs previous version
5. Imported opponent ideas (accepted/rejected/deferred)
6. Risk register
7. Test and QA gates
8. DoD checklist
9. Next round strategy
10. Now/Next/Blockers

Absorption rules in FINAL
- Import at least 3 opponent ideas.
- Reject at least 1 weak own idea with reason.
- Keep tests and DoD verifiable.
