# RUBRIC SCORE - Tournament V2

## 0) Purpose
- Shared scoring framework for operator + @clems.
- Used for R1 ranking and R2 final selection.

## 1) Weighted criteria (100 base)
- Stability and reliability: 35
- Architecture and engineering quality: 30
- Clarity and vulgarisation quality: 20
- Resource feasibility: 15

## 2) Bonus and penalties
- Bonus up to +10:
  - deterministic replay design is complete and testable
  - skill lock and trust model is auditable
  - eval harness has actionable non-regression gates
- Penalty up to -20:
  - approval/security boundary violations
  - non-reproducible plan sections
- Hard disqualification:
  - cross-project memory design without strict isolation
  - proposal bypasses @clems approval for full access
  - missing mandatory package files

## 3) Scoring scale per criterion
Use 0/1/3/5 per sub-dimension.
- 0 = absent or unsafe
- 1 = weak, incomplete
- 3 = acceptable, actionable
- 5 = strong, decision-complete

### 3.1 Stability and reliability (35)
Sub-dimensions:
- durability and atomic persistence
- crash recovery and replayability
- failure containment and fallback behavior
- deterministic execution boundaries

Scoring guidance:
- 0: no real failure strategy
- 1: partial handling, unclear recovery
- 3: clear mechanisms, limited depth
- 5: complete reliability model with verification gates

### 3.2 Architecture and engineering quality (30)
Sub-dimensions:
- module boundaries and contracts
- dependency management and sequencing
- testability and operational clarity
- rollback and migration strategy

Scoring guidance:
- 0: vague architecture
- 1: concepts only, no contracts
- 3: structured and buildable
- 5: implementation-ready with explicit contracts

### 3.3 Clarity and vulgarisation quality (20)
Sub-dimensions:
- readability for operator
- diagram usefulness and correctness
- actionability of roadmap and ticketing
- information density without overload

Scoring guidance:
- 0: unreadable or missing
- 1: high ambiguity
- 3: understandable and usable
- 5: immediate operator clarity under pressure

### 3.4 Resource feasibility (15)
Sub-dimensions:
- token/API budget realism
- hardware and runtime assumptions
- time/team capacity realism
- sensitivity and break-even reasoning

Scoring guidance:
- 0: no numbers
- 1: rough guesses only
- 3: quantified baseline scenarios
- 5: strong resource model with trade-off logic

## 4) Required evidence checks
Before scoring, verify:
- evidence floor achieved:
  - >=8 primary papers
  - >=6 repos
  - >=2 official specs/docs
- assumption labeling is explicit
- mandatory files are present

## 5) Tie-break policy
If total score ties:
1. highest stability score wins
2. then highest architecture score
3. then lowest risk exposure in recommendation
4. then lowest resource risk

## 6) Score sheet template (per competitor)
- competitor_id:
- round:
- evaluator:
- date:

Criterion table:
- stability_score_35:
- quality_score_30:
- clarity_score_20:
- feasibility_score_15:
- bonus_plus_10:
- penalty_minus_20:
- total_score:
- disqualified: yes/no
- disqualification_reason:

Decision summary:
- top strengths:
- top weaknesses:
- required imports for next round:
- blockers:

## 7) Two-evaluator consistency check
- Both evaluators score independently.
- Compare totals and criterion deltas.
- If absolute delta > 10 points, run reconciliation review:
  - identify criterion disagreements
  - align on evidence interpretation
  - log final agreed score

## 8) Confidentiality rule
- Detailed numeric breakdown is for operator + @clems.
- Competitors receive only:
  - verdict
  - required imports
  - blockers
