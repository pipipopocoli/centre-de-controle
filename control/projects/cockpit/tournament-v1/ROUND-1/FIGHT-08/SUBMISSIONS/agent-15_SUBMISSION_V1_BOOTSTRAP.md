Objective
- Stabilize Cockpit V1: UI baseline, docs/runbook, setup hygiene, MCP wiring aligned to canonical state schema.

Scope in/out
- In: define L1 delivery slices for UI scaffold, docs/runbook, setup fixes, MCP wire + state schema migration.
- In: specify verifiable tests and DoD artifacts.
- Out: deep refactors, new features beyond V1 stabilization, non-critical UX polish.

Architecture/workflow summary
- Phase Plan: lock objective, scope, risks, and decisions in DECISIONS.md when needed.
- Phase Implement: UI scaffold + docs/runbook + setup hygiene + MCP wiring to canonical state schema.
- Phase Test: minimal e2e scenario, schema validation, smoke checks.
- Phase Review: doc pass, verify DoD artifacts, ensure rollback path.
- Phase Ship: merge, tag/release if required.

Changelog vs previous version
- Initial bootstrap submission for R16 F08 (L1).

Imported opponent ideas (accepted/rejected/deferred)
- None yet (opponent bootstrap not provided). Deferred to final.

Risk register
- MCP protocol drift vs app server expectations.
- Partial migration of state schema leading to inconsistent UI.
- Setup instability from env drift (venv, deps, .app artifacts).

Test and QA gates
- Manual: verify required sections and ASCII-only content in submission.
- Manual: confirm Now/Next/Blockers present at end.
- Manual: check proposed tests are concrete and runnable.

DoD checklist
- Output verifiable (submission with required sections).
- Risks listed with at least one mitigation idea in final.
- Docs/state update plan is explicit.
- Reversible approach described (rollback or revert path).

Next round strategy
- Absorb >=3 opponent ideas, reject >=1 weak own idea with reason.
- Tighten tests into exact commands and minimal e2e flow.
- Clarify scope boundaries and acceptance criteria.

Now/Next/Blockers
- Now: Bootstrap submitted.
- Next: Read opponent bootstrap, write final with absorption rules.
- Blockers: Missing opponent bootstrap file for Phase B.
