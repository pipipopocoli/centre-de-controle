# TEMPLATE PLAN 40 DEVS - Mandatory structure

## 0) Metadata
- plan_id:
- author:
- date:
- round:
- scope:
- status:

## 1) Executive summary
- Decision summary:
- Why now:
- What changes first:
- What is deferred:
- Success definition:

## 2) System context and constraints
- Product context:
- Technical context:
- Locked constraints:
- Non-goals:
- Approval boundaries:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 3) Modules and interface contracts
For each module:
- module_name:
- responsibility:
- inputs:
- outputs:
- api_contract:
- error_contract:
- dependency_list:
- owner_role:

Mandatory modules to cover:
- WorkspaceManager
- PolicyEngine
- ToolSkillRegistry
- AgentRunnerOrchestrator
- MemoryEngine
- ObservabilityEvalHarness
- VulgarisationGenerator

## 4) Data model, event streams, persistence
- Entity model:
- Event model:
- Persistence model:
- Indexing model:
- Retention and deletion policy:
- Corruption recovery model:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 5) Orchestration flow and failure modes
- State machine:
- Queue strategy:
- Retry policy:
- Timeout policy:
- Backoff policy:
- Circuit breaker:
- Dead letter handling:
- Recovery flow:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 6) Memory design
- Project isolation rules:
- Global Brain promotion rules:
- Compaction strategy:
- Retrieval policy:
- Contamination prevention:
- Auditability:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 7) Skills and souls operating model
- Souls model:
- Skills taxonomy:
- Skill lifecycle:
- Permission matrix:
- Trust tiers:
- Approval flow:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 8) Eval harness and non-regression gates
- Task corpus:
- Bench strategy:
- Metrics:
- Regression thresholds:
- Replay bundle format:
- Gate policy:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 9) WBS and execution plan
- Epic list:
- Workstreams:
- Milestones:
- Dependencies:
- Critical path:

Ticket table (mandatory)
- ticket_id
- title
- owner_role
- dependency_ids
- estimate
- risk_level
- dod
- test_evidence
- rollback

## 10) Risks, mitigations, kill-switch
- Top risks:
- Risk score method:
- Mitigation per risk:
- Trigger thresholds:
- Kill-switch criteria:
- Incident command protocol:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 11) DoD, test plan, rollout/rollback
- DoD global:
- Test matrix:
- Rollout phases:
- Rollback plan:
- Observability checkpoints:
- Sign-off roles:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 12) Resource budget
- Token/API budget:
- Hardware budget:
- Time budget:
- Team bandwidth model:
- Cost sensitivity model:
- Break-even assumptions:

Required fields:
- inputs:
- outputs:
- owner:
- acceptance_criteria:
- verification_command_or_evidence:

## 13) Assumptions register
For each assumption:
- assumption_id
- statement
- risk_if_wrong
- validation_action
- deadline
- owner

## 14) Open decisions register
For each decision:
- decision_id
- question
- options
- recommendation
- owner
- due_date

## 15) Appendix
- References:
- Glossary:
- Change log:
