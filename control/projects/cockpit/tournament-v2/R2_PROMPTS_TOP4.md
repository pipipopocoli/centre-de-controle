## RECOVERY RELAUNCH 2026-02-18

- Scope lock: cockpit only
- SLA first deposit: <= 6h
- Mandatory status cadence: every 2h (Now / Next / Blockers)
- Mandatory first artifacts per finalist:
  - 00_COMPARISON_MATRIX.md
  - 00_MERGE_RECOMMENDATION.md
- Reminder: keep non-negotiable constraints active (isolation, approvals, souls Option A).

# R2 Prompts Top4 - Ready To Send

## R2 mode lock
- Round: R2 top4 fusion (competitors are now aware of all R1 options).
- Entrants:
  - competitor-r1-b
  - competitor-r1-c
  - competitor-r1-f
  - competitor-r1-e
- Non-negotiable constraints remain active:
  - Global Brain accessible for generic learnings only.
  - Project memory isolation by default.
  - Souls Option A fixed.
  - Skills executable, workspace-only by default.
  - Full access actions need @clems approval.

## Dispatch lines (copy/paste)
- Tu es competitor-r1-b. Lis ton prompt R2 ci-dessous et ecris dans: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2/competitor-r1-b/
- Tu es competitor-r1-c. Lis ton prompt R2 ci-dessous et ecris dans: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2/competitor-r1-c/
- Tu es competitor-r1-f. Lis ton prompt R2 ci-dessous et ecris dans: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2/competitor-r1-f/
- Tu es competitor-r1-e. Lis ton prompt R2 ci-dessous et ecris dans: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R2/competitor-r1-e/

## Universal R2 prompt (paste as-is)

```md
R2 MISSION - TOP4 FUSION (aware mode)

Context
- Tu es en Round 2 du Tournoi V2.
- Tu peux lire toutes les options R1 et tu dois produire une fusion meilleure, plus claire, plus faisable.
- Respect strict des contraintes lockees (isolation projet, approval @clems, Option A souls, workspace-only default).

Mandatory outputs (write only in your R2 folder)
1) 00_COMPARISON_MATRIX.md
2) 00_MERGE_RECOMMENDATION.md
3) 01_EXEC_SUMMARY.md
4) 02_ARCHITECTURE.md
5) 03_MEMORY_SYSTEM.md
6) 04_SKILLS_AND_SOULS.md
7) 05_EVAL_HARNESS.md
8) 06_ROADMAP_40DEVS.md
9) 07_RESOURCE_BUDGET.md
10) 08_VULGARISATION_SPEC.md
11) PROMPTS/ (implementation prompts package)
12) EVIDENCE/ (sources + assumptions + claim trace)

Hard requirements
- Build a conscious fusion from all 6 R1 options.
- In 00_COMPARISON_MATRIX.md, include for each competitor: Adopt / Reject / Defer + rationale.
- In 00_MERGE_RECOMMENDATION.md, output one final architecture and one execution roadmap.
- Quantify resources (tokens/API/hardware/time) with scenario model.
- Keep all claims source-backed or tagged ASSUMPTION with validation plan.

Quality bar
- Decision-complete, implementation-ready, no vague sections.
- Include rollback strategy per major module.
- Include release gates and non-regression criteria.
- Include operator-first vulgarisation spec executable offline.

Do not
- Do not violate isolation rules.
- Do not propose implicit full-access without @clems approval.
- Do not omit comparison/adoption rationale.
```

## Required import seeds per finalist

### competitor-r1-b
- Import required:
  - competitor-r1-c queue fairness + anti-thundering-herd scheduler policy.
  - competitor-r1-f pressure-mode UX hierarchy and action-first cards.
  - competitor-r1-e FP/FN calibrated release gates.

### competitor-r1-c
- Import required:
  - competitor-r1-b trust-tier lifecycle + strict skills.lock controls.
  - competitor-r1-f operator comprehension constraints (60-second path).
  - competitor-r1-e release packet discipline and hard/soft gate structure.

### competitor-r1-f
- Import required:
  - competitor-r1-b supply-chain trust and provenance hardening.
  - competitor-r1-c fallback tier and queue fairness contracts.
  - competitor-r1-e benchmark and non-regression gating discipline.

### competitor-r1-e
- Import required:
  - competitor-r1-c orchestration and scheduler-level resilience design.
  - competitor-r1-b skill governance and revocation framework.
  - competitor-r1-f pressure UX and local dashboard clarity contract.

## Reminder
- R2 requires the two mandatory files:
  - 00_COMPARISON_MATRIX.md
  - 00_MERGE_RECOMMENDATION.md
- Any missing mandatory artifact means non-compliant package.
