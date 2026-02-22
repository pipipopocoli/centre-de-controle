# TOURNAMENT PROMPT R1 - V2 (6 competitors isolated)

## 0) Operator header
- Mode: Round 1 isolated.
- Competitors cannot read other competitor outputs.
- Goal: produce 6 distinct, evidence-backed plans for Cockpit V2.
- Priority order: stability, quality, clarity, feasibility.
- Scope: plan only. No production code changes in this round.

## 1) Locked constraints (non negotiable)
- Global Brain must stay available for generic skills, souls, protocols, and generic learnings.
- Project memory must stay isolated. No cross-project retrieval for conversations, logs, artifacts, or run data by default.
- Souls model is Option A:
  - Persistent souls: clems (L0), victor (L1), leo (L1).
  - Workers are ephemeral and project-scoped.
- Skills are executable in V2 but default execution scope is workspace-only.
- Any full access action requires @clems approval:
  - Outside workspace read/write.
  - Deep refactors or wide folder surgery.
  - New external skill install or major skill update.
  - API spend beyond baseline subscription assumptions.
  - Off-mission tasks.
- The target quality bar is "40 dev team" planning depth.

## 2) Required output package per competitor
Write exactly these files under:
`/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/<competitor_id>/`

1. `01_EXEC_SUMMARY.md`
2. `02_ARCHITECTURE.md`
3. `03_MEMORY_SYSTEM.md`
4. `04_SKILLS_AND_SOULS.md`
5. `05_EVAL_HARNESS.md`
6. `06_ROADMAP_40DEVS.md`
7. `07_RESOURCE_BUDGET.md`
8. `08_VULGARISATION_SPEC.md`
9. `PROMPTS/` (implementation prompt set for clems/victor/leo/workers, Codex + Antigravity variants)
10. `EVIDENCE/` (citations, links, assumptions table)

## 3) Evidence minimum (hard gate)
- At least 8 primary papers.
- At least 6 open-source repositories.
- At least 2 official specs/docs.
- Every major claim must be either:
  - Source-backed, or
  - Marked as `ASSUMPTION` with validation plan.

## 4) Strict plan format
Each main markdown file must include:
- Context
- Problem statement
- Proposed design
- Interfaces and contracts
- Failure modes
- Validation strategy
- Rollout/rollback
- Risks and mitigations
- Resource impact

Additionally, include these artifacts in `06_ROADMAP_40DEVS.md`:
- Work breakdown structure by workstream.
- Ticket table with:
  - ticket_id
  - owner_role
  - dependency_ids
  - dod
  - test_evidence
  - risk_level

## 5) Global technical topics to cover deeply
- Distributed-like orchestration patterns for many agents.
- Durable execution and deterministic replay.
- Memory stack design:
  - FTS baseline
  - optional semantic layer
  - compaction/summarization
  - promotion rules into Global Brain
- Non-regression evaluation harness.
- Policy and approvals model.
- Resource budget and operating envelope.

## 6) Prohibited shortcuts
- No shallow architecture diagrams without contracts.
- No "just trust this" claims.
- No suggestion that violates project isolation.
- No full access step without explicit approval gate.

## 7) Base prompt template (generic copy/paste)
Use this template for each competitor and then append the axis-specific addendum.

```
ROLE
You are a senior researcher-engineer (systems + reliability + product).

MISSION
Produce a full Cockpit V2 tournament package for Round 1.
This is a planning/research round. Do not modify production runtime code.

LOCKED CONSTRAINTS
- Global Brain always available, promotion only by @clems.
- Project memory isolated by default.
- Souls Option A: persistent clems/victor/leo, ephemeral workers.
- Skills executable, default workspace-only.
- Full access actions require @clems approval.
- Priority: stability > quality > clarity > feasibility.

OUTPUT PATH
/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/<competitor_id>/

REQUIRED FILES
1) 01_EXEC_SUMMARY.md
2) 02_ARCHITECTURE.md
3) 03_MEMORY_SYSTEM.md
4) 04_SKILLS_AND_SOULS.md
5) 05_EVAL_HARNESS.md
6) 06_ROADMAP_40DEVS.md
7) 07_RESOURCE_BUDGET.md
8) 08_VULGARISATION_SPEC.md
9) PROMPTS/
10) EVIDENCE/

STRICT DEPTH
- Architecture + interfaces + data model + streams.
- WBS for 40-dev team with ticketized execution.
- Prompt pack for implementation agents.
- Every major claim source-backed or marked ASSUMPTION.

EVIDENCE FLOOR
- >=8 primary papers
- >=6 repos
- >=2 official specs/docs

QUALITY BAR
- Decision-complete and execution-ready.
- Explicit rollback and failure handling.
- Resource budget realistic for tokens/API/hardware/time.
```

## 8) Axis variants (append to generic prompt)

### Variant A - Stability and persistence
- Focus on atomic persistence, crash recovery, replayability, and corruption prevention.
- Define deterministic run bundle contract.
- Include explicit state machine for retries/timeouts/backoff.

### Variant B - Skills supply chain
- Focus on skill registry, trust tiers, lockfile, pin commit, review workflow.
- Define install/update/revoke lifecycle.
- Include attack surface analysis and containment policy.

### Variant C - Router and orchestration graph
- Focus on runtime router design across Codex/Antigravity/optional providers.
- Define scheduling policy, queue model, and fallback tiers.
- Include anti-thundering-herd and fairness logic.

### Variant D - Memory engine
- Focus on project memory isolation plus Global Brain promotion.
- Define chunking/indexing/retention/compaction/expiry.
- Include retrieval policy and contamination guardrails.

### Variant E - Eval harness and regression gates
- Focus on benchmark selection, replay packs, patch quality metrics.
- Define regression gates and release-blocking thresholds.
- Include false positive/false negative handling.

### Variant F - UX vulgarisation and operator clarity
- Focus on vulgarisation tab UX and readability under pressure.
- Define dashboard contracts, visual hierarchy, update cadence.
- Include "60-second operator comprehension" acceptance test.

## 9) R1 manual dispatch block (copy/paste)
- Tu es competitor-r1-a. Lis le prompt generique + Variant A (stability/persistence). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-a/`
- Tu es competitor-r1-b. Lis le prompt generique + Variant B (skills supply chain). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-b/`
- Tu es competitor-r1-c. Lis le prompt generique + Variant C (router/orchestration). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-c/`
- Tu es competitor-r1-d. Lis le prompt generique + Variant D (memory engine). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-d/`
- Tu es competitor-r1-e. Lis le prompt generique + Variant E (eval harness). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/`
- Tu es competitor-r1-f. Lis le prompt generique + Variant F (ux vulgarisation). Output path: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-f/`

## 10) R1 acceptance checklist
- All required files exist.
- Evidence floor reached.
- No hard constraint violation.
- Plan is decision-complete and ticketized.
- Resource budget is explicit and testable.
