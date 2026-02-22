# MISSION-NOVA-WAVE09-RESEARCH

Objective
- Run Nova as dual-lane L1:
  - lane A: vulgarisation operator-first,
  - lane B: deep scientific RnD scouting with actionable proposals.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`

Scope (Out)
- Tournament activation
- Destructive cleanup
- Cross-project retrieval

Cadence
- Report every 2h with `Now/Next/Blockers`.
- Deliver one deep RnD item per checkpoint.

Done
- Every recommendation includes:
  - owner
  - next action
  - evidence path
  - decision tag: adopt/defer/reject
- Brief 60s always present.
- Scientific watch always present.

## Deep prompt by phase (copy/paste)

### PLAN prompt
```md
@nova
Focus (PLAN)
- Identify 3 high-value research questions for current Cockpit scope.
- For each: why now, expected impact, and what proof would validate it.

Output required
- Brief 60s
- Research table (question, sources, confidence, risk)
- Top recommendation with owner/action/evidence
```

### IMPLEMENT prompt
```md
@nova
Focus (IMPLEMENT)
- Propose 2 implementation candidates based on fresh research signals.
- Include one code-level proposal (snippet/pseudocode) and one process-level proposal.

Output required
- Brief 60s
- Candidate A/B with cost/time/risk/fallback
- Adopt/defer/reject recommendation
```

### TEST prompt
```md
@nova
Focus (TEST)
- Define scientific validation gates for the selected proposal.
- Include metrics, thresholds, and anti-regression checks.

Output required
- Brief 60s
- Validation protocol (metric, threshold, sample size)
- Decision recommendation with evidence path
```

### REVIEW prompt
```md
@nova
Focus (REVIEW)
- Consolidate what was learned and classify all recommendations.
- Produce decision ledger with accepted/deferred/rejected and rationale.

Output required
- Brief 60s
- Decision ledger (owner/action/evidence/decision)
- Top residual risks and mitigation
```

### SHIP prompt
```md
@nova
Focus (SHIP)
- Publish the state-of-the-art delta for this cycle.
- List new technologies/literature to track next cycle.

Output required
- Brief 60s
- What changed vs previous cycle
- Next watchlist and first action item
```
