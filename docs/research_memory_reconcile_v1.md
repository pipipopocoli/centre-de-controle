# Memory Reconcile V1 (Operational vs Architecture)

## Scope
- Project lock: `cockpit`
- Goal: reconcile short-term run-loop reality with long-term memory architecture ideas.

## Source A - Agent-9 operational evidence
- Runtime path:
  - `~/Library/Application Support/Cockpit/projects/cockpit/agents/agent-9/state.json`
  - `~/Library/Application Support/Cockpit/projects/cockpit/agents/agent-9/journal.ndjson`
- Observed:
  - Focus is run-loop operations (mentions, reply_ack, request_closed).
  - No memory index design, no retrieval schema, no vector pipeline.
  - Useful for KPI and lifecycle truth (what really happened in prod runtime).

## Source B - Leo architecture research
- Doc:
  - `/Users/oliviercloutier/Desktop/Cockpit/docs/research_agent_architecture_v2.md`
- Observed:
  - Strategic exploration: skills standard, vector store, org dashboard, role design.
  - Good backlog for V-next architecture.
  - Not production-ready runtime spec yet.

## Reconcile decision
- Adopt now:
  - Keep run-loop truth from runtime journals/states as gate source.
  - Keep deterministic per-project memory files (`memory.md`, `journal.ndjson`, `DECISIONS.md`).
  - Keep strict isolation by project id.
- Later (paper backlog):
  - Semantic retrieval and vector memory.
  - Agent architecture expansion from Leo doc.
  - Advanced org/task dashboard.
- Reject now:
  - Any cross-project retrieval path.
  - Any non-deterministic memory write in runtime loop.

## Constraints (locked)
- Local-first.
- No API keys required for automation flow.
- Non-destructive memory updates (proposal files first, no blind overwrite).

## Execution note
- Until gate KPIs are stable, memory changes stay paper-first.
- Runtime code path remains focused on dispatch lifecycle correctness and observability.
