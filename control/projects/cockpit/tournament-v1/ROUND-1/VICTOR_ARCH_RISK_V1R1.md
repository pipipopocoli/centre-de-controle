# Round 1 - Victor Arch Risk V1R1

## Context Lock
- PROJECT LOCK: cockpit
- Base source: /Users/oliviercloutier/Desktop/Cockpit/docs/cockpit_v2_project_spec.md
- Input: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/LEO_BIBLE_OWNER_V1R1.md
- Date reference: 2026-02-13

## Objective
- Harden V1 with architecture clarity, risk controls, process invariants, and reversible implementation sequence.

## Target V1 Architecture (Simplified)
1. Source of truth
- Project context: selected left project only.
- Agent registry: one JSON source.
- Workflow truth: STATE.md + tournament docs until implementation kickoff.

2. Core runtime path
- Operator input -> L0 orchestration -> L1 lead handoff -> L2 specialist execution.
- All writes require explicit project_id.
- Status writes require canonical status set + timestamp.

3. Safety path
- Runtime dispatch failure -> fallback provider -> retry queue -> blocker state if exhausted.
- Build mismatch -> non-blocking warning + rebuild guidance.

## Invariants (Must Never Break)
- INV-01: no post_message write without explicit project_id.
- INV-02: metadata.project_id cannot mismatch payload project_id.
- INV-03: startup project must come from last valid selection, not hardcoded demo.
- INV-04: one task has one owner.
- INV-05: state transition must pass status model matrix.
- INV-06: release gate cannot pass without evidence pack.

## Architecture/Risk Change Proposals

### VIC-C01
- Problem: project context can drift on startup.
- Proposal: session resolver with strict fallback order and persistence.
- Impact: deterministic startup context.
- Cost: low.
- Risk: stale session file if project removed.
- Dependencies: session state module.
- Test: startup scenarios A/B/C with deleted project edge case.
- DoD: 100 percent startup tests pass.

### VIC-C02
- Problem: weak payload validation allows silent writes.
- Proposal: hard validation layer for post_message payload and metadata coherence.
- Impact: prevents cross-project contamination.
- Cost: low.
- Risk: stricter API may break old clients.
- Dependencies: MCP server contract update.
- Test: invalid payload suite with negative cases.
- DoD: all invalid payloads rejected with explicit error.

### VIC-C03
- Problem: fallback logic is implicit.
- Proposal: explicit routing contract with primary/fallback/retry states.
- Impact: predictable failure handling.
- Cost: medium.
- Risk: extra state complexity.
- Dependencies: platform router policy.
- Test: fault injection on primary runtime.
- DoD: fallback path exercised and logged.

### VIC-C04
- Problem: technical status values are not bounded.
- Proposal: status enum registry with validation gate at write time.
- Impact: no invalid status pollution.
- Cost: low.
- Risk: migration effort for old values.
- Dependencies: status map file.
- Test: write invalid status and assert failure.
- DoD: no unknown status in persisted state.

### VIC-C05
- Problem: quality gates are informal.
- Proposal: gate manifest file with command list and required evidence type.
- Impact: repeatable release checks.
- Cost: low.
- Risk: stale manifest if not maintained.
- Dependencies: test inventory.
- Test: run manifest parser and gate dry run.
- DoD: gate passes only with complete evidence.

### VIC-C06
- Problem: rollback path depends on tribal memory.
- Proposal: release snapshot format with rollback steps per lot.
- Impact: safer hotfix and rollback.
- Cost: medium.
- Risk: overhead per release.
- Dependencies: release note format.
- Test: rollback drill in staging sandbox.
- DoD: rollback executed in <= 10 min.

### VIC-C07
- Problem: no dependency graph for lot ordering.
- Proposal: lot dependency matrix with hard/soft dependencies.
- Impact: avoids impossible sequencing.
- Cost: medium.
- Risk: matrix maintenance burden.
- Dependencies: workstream split.
- Test: topological sort without cycle.
- DoD: no cycle in implementation lots.

### VIC-C08
- Problem: branch state confusion causes version mismatch.
- Proposal: display stamp, head, and branch in header with warning rules.
- Impact: faster diagnosis.
- Cost: low.
- Risk: missing git in packaged app.
- Dependencies: UI banner support.
- Test: simulate detached and missing git cases.
- DoD: banner degrades gracefully.

### VIC-C09
- Problem: mission prompts vary and miss required fields.
- Proposal: prompt schema linter for project lock, owner, DoD, output path.
- Impact: reduces malformed dispatches.
- Cost: medium.
- Risk: false positives in lint.
- Dependencies: template standardization.
- Test: lint pass rate on sample prompt set.
- DoD: 100 percent production prompts pass lint.

### VIC-C10
- Problem: no explicit process for unresolved critical risk.
- Proposal: veto process with owner and unblock options.
- Impact: safer go/no-go decisions.
- Cost: low.
- Risk: decision delays.
- Dependencies: scorecard section.
- Test: simulated risk veto scenario.
- DoD: veto path documented and rehearsed.

### VIC-C11
- Problem: runtime contracts lack failure codes.
- Proposal: define normalized error codes and operator-facing messages.
- Impact: better triage speed.
- Cost: medium.
- Risk: initial migration cost.
- Dependencies: MCP and UI error handling.
- Test: error code coverage report.
- DoD: every failure mode maps to one code/message.

### VIC-C12
- Problem: no accountability for stale docs.
- Proposal: doc freshness SLA: STATE daily, ROADMAP weekly, Bible per gate.
- Impact: current source of truth.
- Cost: low.
- Risk: administrative overhead.
- Dependencies: owner assignment.
- Test: freshness checker script output.
- DoD: freshness breaches alert in daily check.

### VIC-C13
- Problem: workload spikes collapse lead capacity.
- Proposal: enforce lead concurrency budget and queue overflow policy.
- Impact: stable throughput.
- Cost: medium.
- Risk: longer queue time.
- Dependencies: status counters.
- Test: load simulation with 2x queue.
- DoD: no lead exceeds concurrency cap.

### VIC-C14
- Problem: no contract for evidence naming.
- Proposal: evidence path convention by round, gate, and issue.
- Impact: faster audit.
- Cost: low.
- Risk: migration work.
- Dependencies: release manifest.
- Test: validator checks naming convention.
- DoD: 100 percent new evidence follows convention.

### VIC-C15
- Problem: planning outputs are detailed but not executable.
- Proposal: each chapter ends with concrete implementation lot references.
- Impact: clear path from plan to code.
- Cost: medium.
- Risk: chapter clutter.
- Dependencies: lot matrix.
- Test: trace one requirement to one lot.
- DoD: traceability matrix complete.

### VIC-C16
- Problem: no guard against hidden cross-project writes in tests.
- Proposal: test harness that fails if unexpected project files change.
- Impact: catches contamination.
- Cost: medium.
- Risk: brittle on noisy files.
- Dependencies: test harness wrappers.
- Test: intentional wrong write should fail harness.
- DoD: harness integrated in gate.

### VIC-C17
- Problem: no runtime health objective.
- Proposal: set SLOs for dispatch success, fallback rate, and ack latency.
- Impact: measurable reliability.
- Cost: medium.
- Risk: SLO churn early in V1.
- Dependencies: observability fields.
- Test: weekly SLO report generation.
- DoD: first baseline SLO report published.

### VIC-C18
- Problem: outlier proposals can derail V1 scope.
- Proposal: outlier intake rubric with strict accept criteria.
- Impact: innovation without destabilization.
- Cost: low.
- Risk: blocking useful novelty.
- Dependencies: Round 2 process.
- Test: apply rubric to 5 outlier ideas.
- DoD: accepted outliers have clear V1 fit.

### VIC-C19
- Problem: no formal go/no-go checklist before code.
- Proposal: pre-implementation gate requiring all tournament outputs complete.
- Impact: prevents ambiguous kickoff.
- Cost: low.
- Risk: timeline pressure.
- Dependencies: all rounds complete.
- Test: checklist simulation with one missing file.
- DoD: kickoff blocked when checklist incomplete.

### VIC-C20
- Problem: hidden dependency on old CP-01 docs.
- Proposal: mark CP-01 docs as archived context, not active source.
- Impact: prevents priority conflict.
- Cost: low.
- Risk: losing historical details if unlinked.
- Dependencies: roadmap rebase.
- Test: grep source references for CP-01 usage.
- DoD: active docs point only to V1 tournament source.

### VIC-C21
- Problem: no explicit migration path from tournament docs to implementation issues.
- Proposal: issue generation protocol from winner doc sections.
- Impact: immediate execution readiness.
- Cost: medium.
- Risk: rigid issue breakdown.
- Dependencies: final winner.
- Test: generate 10 sample issues from sections.
- DoD: every issue has owner, DoD, and gate link.

### VIC-C22
- Problem: blocker escalation rule is broad.
- Proposal: 60-min blocker policy with two options + recommendation mandatory.
- Impact: faster decision velocity.
- Cost: low.
- Risk: shallow analysis under time pressure.
- Dependencies: operating system rules.
- Test: review blocker logs for complete format.
- DoD: 100 percent blocker reports follow template.

## Coherence Matrix (Leo vs Runtime Constraints)
| Area | Leo direction | Runtime constraint | Verdict | Mitigation |
|---|---|---|---|---|
| Status V4 | 4 business states | many raw technical states | Accept with mapper | keep raw status as secondary |
| 60-second readability | high visibility | UI space limits | Accept | strict card signal cap |
| Program Bible depth | very detailed | operator time budget | Accept with structure | action block first in each chapter |
| Visual density | rich views | Qt layout complexity | Partial | phase visual features by lot |
| Outlier tracks | required | scope risk | Accept with rubric | gate by feasibility and risk |

## Implementation Lots (Reversible)
1. Lot A: doc and governance lock.
2. Lot B: context routing hardening.
3. Lot C: status model and UI mapping.
4. Lot D: version visibility and gate tooling.
5. Lot E: final pre-implementation issue generation.

## Round 1 Self-Gate
- Change proposals count: 22 (target >= 20).
- Each proposal has impact/cost/risk/dependencies/test/DoD.
- Architecture/risk angle preserved with executable constraints.

## Now / Next / Blockers
- Now: architecture hardening, invariant set, and risk controls drafted.
- Next: stress test Leo proposals against Round 2 critiques and final gates.
- Blockers: none.
