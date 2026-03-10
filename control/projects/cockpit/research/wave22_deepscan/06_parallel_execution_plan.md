# Wave22 Parallel Execution Plan

## Non-negotiable rule
- 10 agents assigned
- 5 active lanes max
- 5 queued/review lanes max

## Models
- Default execution model: Kimi K2.5
- Review rescue: Claude Sonnet 4.6
- Final architecture/release review only: Claude Opus 4.6

## Active Wave A
1. @victor
- Lane: architecture truth map
- Output: repo/system boundary map, ADR delta, source-of-truth matrix

2. @leo
- Lane: desktop shell and UX
- Output: direct lane, room lane, navigation, responsive corrections

3. @nova
- Lane: product research synthesis
- Output: research packet, user-value framing, feature priorities

4. @agent-1
- Lane: OpenRouter/runtime reliability
- Output: direct rescue, room degrade honesty, health and diag cleanup

5. @agent-4
- Lane: repo hygiene and archive decisions
- Output: active-vs-archive list, dead scripts/assets/docs list, safe cleanup set

## Queued Wave B
6. @agent-2
- Lane: strict direct vs room pathway rules

7. @agent-3
- Lane: create/takeover/project summary flows

8. @agent-5
- Lane: storage, DB, backup, state normalization

9. @agent-6
- Lane: tests, bug sweep, broken links, missing wires

10. @agent-7
- Lane: accessibility and responsive closeout

## Monitoring contract
- Each lane posts `Now / Next / Blockers`
- `@clems` collects every 30-45 minutes
- If blocker > 60 min:
  - 2 options
  - 1 recommendation
  - reassignment or escalation

## Immediate monitoring packet
- `@victor`
  - Now: truth-map live boundaries and ADR deltas
  - Next: produce source-of-truth matrix
  - Blockers: none
- `@leo`
  - Now: stabilize desktop shell and direct-vs-room clarity
  - Next: validate responsive and operator readability
  - Blockers: none
- `@nova`
  - Now: synthesize external research into product decisions
  - Next: map research to backlog priorities and decision tags
  - Blockers: none
- `@agent-1`
  - Now: inspect OpenRouter degraded behavior and direct rescue logic
  - Next: tighten diagnostics and room/direct honesty
  - Blockers: none
- `@agent-4`
  - Now: classify legacy docs, scripts, and archive candidates
  - Next: prepare safe cleanup list
  - Blockers: none

## Merge order
1. Truth and research
2. Runtime and chat reliability
3. Shell and UX
4. Project flows
5. Hygiene and cleanup
6. Tests and release proof
