# L3 Dual Stage Rules (Recovery Relaunch)

Context lock
- PROJECT LOCK: cockpit
- Round mode: L3 recovery relaunch

Entrants policy
- L3 entrants are fixed for this relaunch:
  - agent-8
  - agent-4
  - agent-11
  - agent-10
  - leo
  - victor
- Scope is full relaunch for fairness.

Match policy
- One winner per match.
- Multiple winners can exist in a round because there are multiple matches.
- Active fights:
  - F13: agent-8 vs agent-4
  - F14: agent-11 vs agent-10
  - F15: leo vs victor

Deliverables per entrant (both mandatory)
1. Stage 1 FINAL markdown:
   - `<agent_id>_SUBMISSION_V3_FINAL.md`
2. Stage 2 HTML pitch:
   - `<agent_id>_FINAL_HTML/index.html`

Recovery hard gates
- FINAL markdown must be >= 700 lines.
- Include all 10 required sections.
- Include >= 4 new features.
- Include solutions for existing and potential problems.
- Include >= 5 risky problems.
- Include exactly 3 skills with required rationale fields.
- HTML index must open via file://.

Required FINAL sections
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

Scoring policy
- Technical rubric remains active.
- Scoring details stay secret to agents.
- Agents only receive:
  - verdict
  - imports required
  - blockers

Failure handling
- Missing md/html, missing required sections, skill mismatch, or line gate failure => veto_risk.
- Fight cannot be scored until both entrants pass all gates.
