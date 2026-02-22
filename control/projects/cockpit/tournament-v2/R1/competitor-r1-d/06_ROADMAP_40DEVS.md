# 06_ROADMAP_40DEVS - Work breakdown and ticketized execution

## Context
This roadmap turns Variant D into a 40-dev execution program with strict dependencies and evidence-backed DoD.

## Problem statement
Memory work fails when architecture, policy, and QA are delivered out of order. We need dependency-driven sequencing with objective gates.

## Proposed design
### Work breakdown structure (WBS)
- WS1 Program governance and contracts
- WS2 Ingest and immutable segment store
- WS3 FTS index baseline
- WS4 Optional semantic layer
- WS5 Compaction and retention
- WS6 Global Brain promotion controls
- WS7 Policy and approval engine
- WS8 Eval harness and release gates
- WS9 Operator visibility and vulgarisation hooks
- WS10 Rollout, rollback, and incident playbooks

### 40-dev allocation
- WS1: 2
- WS2: 6
- WS3: 5
- WS4: 5
- WS5: 5
- WS6: 3
- WS7: 4
- WS8: 6
- WS9: 2
- WS10: 2

## Interfaces and contracts
- Milestone gate contract
  - gate_id
  - required_tickets
  - pass_criteria
  - evidence_bundle
- Ticket contract
  - ticket_id
  - owner_role
  - dependency_ids
  - dod
  - test_evidence
  - risk_level

## Failure modes
- FM-RD-1: WIP overflow breaks dependency order.
- FM-RD-2: ticket closes without evidence.
- FM-RD-3: semantic work starts before lexical baseline stabilizes.

## Validation strategy
- Weekly gate review using evidence bundles.
- Dependency lint check on ticket table.
- Block merge when required evidence is missing.

## Rollout/rollback
- Rollout by milestones M1-M6.
- Rollback by milestone boundary, not individual ad-hoc patches.

## Risks and mitigations
- Risk: overstaffed parallelism causes integration debt.
  - Mitigation: enforce dependency graph and gate ownership.
- Risk: delayed policy lane blocks release.
  - Mitigation: start WS7 early with mock approvals in WS2.

## Resource impact
- Program span: 6 milestones over ~4 months [ASSUMPTION-A8].
- Requires dedicated platform QA and incident manager rotation.

## Ticket table
| ticket_id | owner_role | dependency_ids | dod | test_evidence | risk_level |
|---|---|---|---|---|---|
| MEM-001 | architect | - | memory contract v1 signed | contract review log | medium |
| MEM-002 | backend | MEM-001 | ingest gateway validates schema+project_id | api contract tests | high |
| MEM-003 | backend | MEM-002 | immutable segment writer with checksums | crash write tests | high |
| MEM-004 | backend | MEM-003 | manifest store with replay pointers | replay integrity suite | high |
| MEM-005 | search | MEM-003 | FTS tokenizer and query path baseline | precision/latency baseline | medium |
| MEM-006 | search | MEM-005 | ranking calibration for lexical mode | p@k benchmark | medium |
| MEM-007 | ml | MEM-005 | semantic embedding queue service | queue reliability tests | medium |
| MEM-008 | ml | MEM-007 | vector index build pipeline | index correctness suite | high |
| MEM-009 | retrieval | MEM-006,MEM-008 | hybrid retrieval router with flags | differential retrieval tests | high |
| MEM-010 | backend | MEM-003 | retention policy scheduler | retention simulation tests | medium |
| MEM-011 | backend | MEM-010 | compaction manifest and provenance links | provenance verification tests | high |
| MEM-012 | backend | MEM-011 | reversible summary generation | rollback drill logs | high |
| MEM-013 | policy | MEM-001 | scope policy engine v1 | role/scope matrix tests | high |
| MEM-014 | policy | MEM-013 | approval token issuance and ttl | token expiry tests | high |
| MEM-015 | policy | MEM-014 | @clems-only promotion gate | negative promotion tests | high |
| MEM-016 | backend | MEM-012,MEM-015 | promotion queue and revocation path | promotion e2e tests | high |
| MEM-017 | qa | MEM-004,MEM-005 | deterministic replay harness v1 | replay determinism report | high |
| MEM-018 | qa | MEM-017 | contamination red-team test suite | contamination report | high |
| MEM-019 | qa | MEM-017,MEM-009 | hybrid quality benchmark pack | quality delta report | medium |
| MEM-020 | sre | MEM-004,MEM-011 | crash recovery automation | chaos run report | high |
| MEM-021 | sre | MEM-020 | incident playbook and runbooks | tabletop drill output | medium |
| MEM-022 | ui | MEM-017 | operator memory status panel contract | ux acceptance checklist | low |
| MEM-023 | qa | MEM-018,MEM-019,MEM-020 | release gate profile | gate threshold report | high |
| MEM-024 | lead | MEM-023 | milestone M4 go/no-go decision | signed decision record | high |
| MEM-025 | sre | MEM-024 | staged rollout + rollback validation | staged rollout logs | high |

## Evidence tags used
[P1][P2][P3][P4][R1][R2][R3][R7][S1][S2][ASSUMPTION-A8]
