# eval_contracts

## Metadata
- stream: S5
- layer: L5
- owner: competitor-r1-e
- approval_ref: not_required_workspace_only
- objective: implement CAP-L5-001..CAP-L5-006 eval harness contracts

## Capability mapping
| capability_id | interface | test_gate | status |
|---|---|---|---|
| CAP-L5-001 | scenario_registry | benchmark catalog versioning pass | implemented |
| CAP-L5-002 | replay_schema | replay bundle schema validation pass | implemented |
| CAP-L5-003 | metrics_schema | gate threshold parser and validation pass | implemented |
| CAP-L5-004 | calibration_model | fp/fn confusion matrix target pass | implemented |
| CAP-L5-005 | release_policy | pass/soft_fail/hard_fail policy applied | implemented |
| CAP-L5-006 | override_audit | override requires approval + rationale | implemented |

## Eval schema contract
Required fields:
- scenario_id
- suite_id
- metrics
- thresholds
- verdict
- override_ref
- override_rationale

Rules:
- schema validation is hard fail on missing required fields
- threshold parser only accepts canonical operators (`=`, `>=`, `<=`, `between`)
- verdict policy supports pass, soft_fail, hard_fail, override

## Release verdict policy
- pass: release lane open
- soft_fail: release lane conditional with owner ack
- hard_fail: release lane blocked
- override: requires explicit approval_ref and rationale, then audit log append

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/eval_contracts.md

## DoD evidence
- CAP-L5-001..CAP-L5-006 are mapped with explicit schema and policy contracts.
- release verdict states are executable and unambiguous.
- override path is approval-gated and auditable by contract.

## test results
- eval_schema_contract_lint: pass
- threshold_parser_contract: pass
- verdict_policy_contract: pass

## rollback note
- if verdict drift appears, freeze override path and restore last validated threshold policy bundle until recalibration is complete.

Now
- L5 eval contract baseline is locked for gate runs.

Next
- execute threshold and calibration evidence reports.

Blockers
- none.
