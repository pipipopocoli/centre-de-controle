# 05_IMPLEMENTATION_PROMPT_PACK

## Dispatch policy
- One stream prompt per layer.
- Each stream must reference capability ids only, no ad-hoc redesign.
- Report format required: Now / Next / Blockers.

## Shared hard constraints for all prompts
- PROJECT LOCK: cockpit
- Use only files under project workspace unless explicit @clems approval exists.
- No cross-project retrieval.
- Any full-access action must include approval_ref.
- Output must include:
  - changed artifacts
  - DoD evidence
  - test results
  - rollback note

## Stream S1 prompt - Reliability core (L1)
```md
Objective
- Implement CAP-L1-001..CAP-L1-006 exactly as defined.

Scope In
- run bundle contract
- append-only event storage
- idempotent transaction boundaries
- crash and corruption recovery routines

Scope Out
- UI rendering and cost analytics

Required outputs
- reliability_contract.md
- replay_validation_report.md
- crash_recovery_test_report.md

Done
- replay determinism gate pass
- crash injection gate pass
- checksum quarantine gate pass
```

## Stream S2 prompt - Skills governance (L2)
```md
Objective
- Implement CAP-L2-001..CAP-L2-007.

Scope In
- skills.lock schema and validator
- trust tiers and lifecycle transitions
- full-access approval gate
- revoke/quarantine pipeline
- runtime conformance tests

Scope Out
- scheduler logic and memory indexing

Required outputs
- skills_policy_spec.md
- conformance_test_report.md
- revoke_drill_report.md

Done
- no elevated action without approval_ref
- codex/antigravity policy parity pass
```

## Stream S3 prompt - Router orchestration (L3)
```md
Objective
- Implement CAP-L3-001..CAP-L3-007.

Scope In
- router front-door contracts
- weighted fair scheduling
- anti-thundering-herd controls
- fallback tier state machine
- provider adapter contracts
- dispatch budget envelopes

Scope Out
- trust-tier governance internals

Required outputs
- router_contracts.md
- scheduler_benchmark_report.md
- fallback_transition_report.md

Done
- starvation test pass
- fallback tier deterministic transition pass
```

## Stream S4 prompt - Memory isolation (L4)
```md
Objective
- Implement CAP-L4-001..CAP-L4-006.

Scope In
- project memory namespace isolation
- FTS baseline retrieval
- optional semantic lane gating
- compaction and retention policies
- promotion gate with de-identification proof

Scope Out
- release verdict UI

Required outputs
- memory_contracts.md
- isolation_test_report.md
- compaction_restore_report.md

Done
- cross-project contamination sentinel pass
- promotion gate approval check pass
```

## Stream S5 prompt - Eval harness (L5)
```md
Objective
- Implement CAP-L5-001..CAP-L5-006.

Scope In
- scenario registry
- replay schema validation
- metrics and threshold policy
- fp/fn calibration
- release verdict policy
- override audit trail

Scope Out
- queue optimization internals

Required outputs
- eval_contracts.md
- threshold_validation_report.md
- calibration_report.md

Done
- pass/soft_fail/hard_fail policy executable
- override path auditable and approval-gated
```

## Stream S6 prompt - UX vulgarisation (L6)
```md
Objective
- Implement CAP-L6-001..CAP-L6-006.

Scope In
- operator summary card hierarchy
- pressure mode behavior
- freshness warnings
- evidence links and fallback tables
- 60-second comprehension drill support

Scope Out
- skill trust lifecycle backend logic

Required outputs
- vulgarisation_ui_spec.md
- comprehension_test_report.md
- accessibility_report.md

Done
- >=85 percent drill accuracy
- stale warning thresholds verified
```

## Stream S7 prompt - Resource/cost/capacity (L7)
```md
Objective
- Implement CAP-L7-001..CAP-L7-006.

Scope In
- cost event schema
- scenario models (small/medium/large/xlarge)
- budget guardrail and alert routing
- capacity SLO contracts
- 40-dev staffing model checks
- break-even matrix

Scope Out
- replay hash algorithm changes

Required outputs
- cost_model_spec.md
- budget_guardrail_report.md
- capacity_slo_report.md

Done
- hard-stop budget rule tested
- break-even matrix reproducible
```

## Integration prompt - Cross-layer lock
```md
Objective
- Validate full cross-layer integration using capability registry.

Checks
- no duplicate ownership per capability_id
- interface coherence across layers
- all gates mapped to executable tests
- unresolved conflicts = 0

Required outputs
- integration_lock_report.md
- final_go_no_go.md

Done
- all checks pass
- rollback map available per layer
```

## Operator dispatch lines (copy/paste)
- Tu es agent-1. Execute Stream S1 L1 Reliability core from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-2. Execute Stream S2 L2 Skills governance from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-3. Execute Stream S3 L3 Router orchestration from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-4. Execute Stream S4 L4 Memory isolation from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-5. Execute Stream S5 L5 Eval harness from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-6. Execute Stream S6 L6 UX vulgarisation from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-7. Execute Stream S7 L7 Resource/cost/capacity from 05_IMPLEMENTATION_PROMPT_PACK.md.
- Tu es agent-8. Execute Integration prompt from 05_IMPLEMENTATION_PROMPT_PACK.md.
