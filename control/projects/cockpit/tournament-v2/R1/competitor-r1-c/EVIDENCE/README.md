# Evidence Pack README

Context
- Evidence folder for competitor-r1-c (Variant C router/orchestration).

Problem statement
- Tournament hard gate requires source-backed claims and explicit assumptions.

Proposed design
- Evidence is split into papers, repos, official docs, claim matrix, and assumptions.

Interfaces and contracts
- Required files:
  - 01_PRIMARY_PAPERS.md
  - 02_OPEN_SOURCE_REPOS.md
  - 03_OFFICIAL_SPECS_DOCS.md
  - 04_CLAIM_MATRIX.md
  - 05_ASSUMPTIONS.md

Failure modes
- Missing floor counts.

Validation strategy
- Primary papers >= 8.
- Open source repos >= 6.
- Official specs/docs >= 2.

Rollout/rollback
- Rollout: reference IDs in all design docs.
- Rollback: block scoring if floor not met.

Risks and mitigations
- Risk: evidence drift between docs.
- Mitigation: claim matrix as source of truth.

Resource impact
- Minimal runtime impact; medium planning rigor impact.
