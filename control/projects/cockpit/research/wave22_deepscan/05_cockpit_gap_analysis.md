# Wave22 Cockpit Gap Analysis

## Live strengths
- Desktop shell and Rust runtime are now clearly the live path.
- OpenRouter-only runtime is already in place.
- Project actions, project summary, voice transcription, and role routing already exist.

## P0 gaps
1. Repo truth is still noisy
- active docs and historical release receipts are mixed in discovery
- legacy references still appear in README, QUICKSTART, installation docs, and some service strings

2. Runtime path split is not fully finished
- desktop app is live, but server/python paths still publish stale `chat/agentic-turn` and `wizard-live` references
- tests still rely heavily on `demo` fixtures

3. Agent operating picture is incomplete
- cards and room surfaces are improving, but repo-level truth and mission tracking are not packaged for sustained execution

4. Governance drift
- STATE/DECISIONS are current, but no Wave22 action packet exists yet

## Architecture synthesis
- Desktop-first is the canonical operator surface.
- Rust core is the live runtime source of truth for direct chat, room orchestration, tasks, takeover, and health.
- Python app/server remain secondary compatibility surfaces and should not define the daily operator path.
- The repo needs a stricter split between:
  - live operator docs and scripts
  - compatibility docs
  - historical receipts and tournament/archive material

## Product synthesis
- `Pixel Home` should optimize for fast direct control: one target, scene awareness, agent observability, and low-latency chat.
- `Le Conseil` should optimize for multi-agent coordination: visible participant outputs, explicit room state, and honest degraded summaries.
- `Overview` should stay read-only and decision-oriented, not a second action room.
- `Docs > Project` should anchor current project truth, not broad multi-project discovery.

## P1 gaps
- deeper repo cleanup of old assets and historical docs
- removal or quarantine of obsolete cloud/server protocol docs
- stronger broken-link policy for active docs
- explicit cost and model observability in project docs

## Archive or drop candidates
- legacy launcher references in active docs
- stale cloud API docs that no longer match local runtime
- examples and tests that still teach `demo` as the default project
