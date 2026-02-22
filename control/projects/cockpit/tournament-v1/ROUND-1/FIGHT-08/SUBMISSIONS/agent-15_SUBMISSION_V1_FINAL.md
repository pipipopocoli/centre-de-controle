Objective
- Stabilize Cockpit V1 (UI + docs + setup + MCP) with verifiable and reversible deliverables.

Scope in/out
- In: L1 delivery slices for UI scaffold, docs/runbook, setup hygiene, MCP wiring aligned to canonical state schema.
- In: short issue to PR to test to review to ship flow with owner unique and WIP <= 5.
- Out: large product refactor, non V1 features, cosmetic polish beyond stabilization.

Architecture/workflow summary
- Phases: Plan -> Implement -> Test -> Review -> Ship.
- Operational control: WIP <= 5, owner unique, declare blocker > 60 min with 2 options + 1 reco.
- Conformance: explicit status when an external input is missing.
- QA gates: ASCII only check, required section check, Now/Next/Blockers footer check.

Changelog vs previous version
- Initial FINAL in recovery mode (no prior FINAL for this agent).

Imported opponent ideas (accepted/rejected/deferred)
- Accepted:
- Keep a short issue -> PR -> test -> review -> ship flow with owner unique.
- Make conformance explicit when external input is missing.
- Add concrete QA gates for ASCII only, required sections, and footer contract.
- Rejected:
- Reject weak own idea: "Wait silently with no provisional final". Reason: no verifiable artifact and no forward progress.
- Deferred:
- None.

Risk register
- Risk: schema drift during MCP wiring.
- Mitigation: state schema validation and explicit changelog per delivery slice.
- Risk: setup instability from env drift.
- Mitigation: documented setup steps and minimal reproducible checks.
- Risk: incomplete absorption of opponent ideas.
- Mitigation: explicit acceptance list and recheck gate.

Test and QA gates
- Gate 1: verify required sections exist in this FINAL.
- Gate 2: verify ASCII only:
- `rg -n '[^\x00-\x7F]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-08/SUBMISSIONS/agent-15_SUBMISSION_V1_FINAL.md || true`
- Gate 3: verify footer contains Now/Next/Blockers.
- Gate 4: spot check scope and risks are explicit and testable.

DoD checklist
- [x] FINAL file present at expected path.
- [x] 10 required sections present.
- [x] ASCII only content.
- [x] QA gates listed and verifiable.
- [x] At least 3 opponent ideas imported.
- [x] One weak own idea rejected with reason.

Next round strategy
- Tighten QA gates into exact commands for minimal e2e scenario.
- Lock acceptance criteria per slice (UI, docs, setup, MCP).
- Keep absorption list explicit and short.

Now/Next/Blockers
- Now: FINAL submitted with absorbed opponent ideas and verifiable gates.
- Next: tighten test commands and add minimal e2e scenario.
- Blockers: None.
