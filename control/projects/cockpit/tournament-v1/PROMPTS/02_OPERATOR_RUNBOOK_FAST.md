# Operator Runbook Fast - Tournament Prompt Loop

## Goal
- Run each tournament round by generating prompts and collecting upgraded submissions.

## 7-step run cycle
1. Pick active fights for current round.
2. For each active agent, collect prior context files.
3. Generate prompt from `01_MATCH_PROMPT_TEMPLATE.md`.
4. Send prompt to agent platform (AG or CDX).
5. Collect submission markdown file.
6. Score and publish judge feedback.
7. Promote winners and generate next round prompts.

## Suggested folder structure
- `ROUND-<n>/FIGHT-<id>/PROMPTS/`
- `ROUND-<n>/FIGHT-<id>/SUBMISSIONS/`
- `ROUND-<n>/FIGHT-<id>/JUDGE_FEEDBACK.md`

## Decision rhythm
- After each fight, decide in 10 minutes:
- winner,
- loser,
- required changes for winner before next round.

## Stop conditions
- Champion selected with no critical unresolved risk.
- Final champion package includes implementation issue map.
- User validation done.

## Failure conditions
- Missing required output sections.
- No measurable complexity increase.
- No opponent idea integration.
- Critical risk not addressed.
