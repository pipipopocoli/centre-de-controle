# PROMPTS Index - competitor-r1-c

Context
- Implementation prompt set for Variant C router/orchestration.

Problem statement
- Execution quality drops when role prompts are generic.

Proposed design
- Provide role-targeted prompts for Codex and Antigravity lanes.

Interfaces and contracts
- Files:
  - CODEX_clems_IMPLEMENT.md
  - CODEX_victor_IMPLEMENT.md
  - CODEX_leo_IMPLEMENT.md
  - CODEX_worker_IMPLEMENT.md
  - AG_clems_IMPLEMENT.md
  - AG_victor_IMPLEMENT.md
  - AG_leo_IMPLEMENT.md
  - AG_worker_IMPLEMENT.md

Failure modes
- Missing owner role or missing done criteria.

Validation strategy
- Every prompt includes objective, scope, constraints, outputs, done, test/qa, risks.

Rollout/rollback
- Rollout in milestone order M1->M4.
- Rollback by disabling workstream prompts and reverting to prior milestone pack.

Risks and mitigations
- Risk: prompt ambiguity.
- Mitigation: strict output paths and verification commands.

Resource impact
- Low runtime impact, high delivery quality impact.
