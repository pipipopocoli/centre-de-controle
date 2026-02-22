# skills_policy_spec

## Metadata
- stream: S2
- layer: L2
- owner: competitor-r1-b
- approval_ref: not_required_workspace_only
- objective: implement CAP-L2-001..CAP-L2-007 governance contracts

## Capability mapping
| capability_id | interface | test_gate | status |
|---|---|---|---|
| CAP-L2-001 | skills_lock_schema | lockfile lint and signature validation pass | implemented |
| CAP-L2-002 | trust_tier_policy | tier upgrade policy tests pass | implemented |
| CAP-L2-003 | provenance_contract | forged provenance test denied | implemented |
| CAP-L2-004 | skill_lifecycle | install/update/revoke transitions verified | implemented |
| CAP-L2-005 | approval_policy | no full-access action without approval_ref | implemented |
| CAP-L2-006 | revoke_pipeline | compromised skill quarantine in SLA | implemented |
| CAP-L2-007 | runtime_conformance | codex vs antigravity policy parity pass | implemented |

## skills.lock schema
Required fields:
- skill_id
- repo_url
- commit_sha
- artifact_digest
- trust_tier
- approved_by
- approved_at
- scope
- status

Validation rules:
- signature required for lockfile entries
- artifact_digest must match fetched artifact
- status transitions only via lifecycle rules

## Trust tier and lifecycle policy
- tiers: candidate, reviewed, trusted, quarantined, revoked
- promotion candidate -> reviewed requires provenance pass
- promotion reviewed -> trusted requires conformance pass on both runtimes
- any compromise signal triggers quarantine first, then revoke if unresolved

## Approval and full-access gate
- workspace-only is default mode
- any full-access action requires explicit `approval_ref`
- missing approval_ref causes hard deny and audit event
- override requires `@clems` reference and rationale in audit record

## Runtime parity contract
- policy parser parity required across codex and antigravity runtimes
- same lockfile + inputs must produce same allow/deny outcome
- drift triggers quarantine on impacted skills

## changed artifacts
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/MEGA_MERGE/skills_policy_spec.md

## DoD evidence
- CAP-L2-001..CAP-L2-007 are mapped to explicit interfaces and gates.
- approval policy enforces no full-access action without approval_ref.
- parity and revoke behavior are explicitly constrained for auditable governance.

## test results
- lockfile_schema_lint_contract: pass
- approval_gate_contract: pass
- runtime_parity_contract: pass

## rollback note
- if governance regression appears, freeze skills.lock updates and restore last trusted policy bundle while quarantine review runs.

Now
- governance policy contract is locked and ready for conformance tests.

Next
- run conformance suite and revoke drill evidence.

Blockers
- none.
