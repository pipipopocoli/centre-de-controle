# SKILLS REPO SHORTLIST - V2 candidate sources

## 0) Policy note
- Status for all entries in this file: `candidate_only`.
- No installation until:
  - pin commit SHA
  - trust tier classification
  - @clems approval

## 1) Shortlist table
| name | usage cible V2 | maturite | risque supply-chain | pourquoi utile | mode sandbox propose | approval policy | status |
|---|---|---|---|---|---|---|---|
| OpenHands (+ SDK) | orchestrated coding agent workflows, tool execution patterns | high | medium | strong real-world multi-step agent execution references | workspace-only first, no external write | reviewed -> @clems approval | candidate_only |
| Continue | IDE-integrated prompt and context workflows | high | medium | useful patterns for context management and developer flow | read-only mirror workspace during eval | reviewed -> @clems approval | candidate_only |
| SWE-agent / SWE-agent-mini | benchmark and patch-loop patterns for code tasks | medium-high | medium | direct relevance for eval harness and regression gates | isolated test workspace, no prod write | reviewed -> @clems approval | candidate_only |
| LangGraph | orchestration graph and state-machine style control | high | medium | clear model for deterministic multi-agent graphs | sandbox runtime with mocked providers | reviewed -> @clems approval | candidate_only |
| Aider | practical edit loop and diff-centric coding UX patterns | high | medium | useful ideas for patch flows and review ergonomics | workspace-only, no git push | reviewed -> @clems approval | candidate_only |
| OpenClaw | competitive architecture reference and operator UX ideas | medium | medium-high | useful for comparative architecture trade-offs | read-only research mode first | untrusted/reviewed -> @clems approval | candidate_only |

## 2) Minimum approval packet per repo
- repo_url
- pinned_commit_sha
- trust_tier
- expected_skill_scope
- security_review_summary
- rollback_plan
- owner_role
- approved_by
- approved_at

## 3) Initial risk checklist
For every candidate before install:
- Does it require broad filesystem access?
- Does it perform network calls by default?
- Does it execute arbitrary shell commands?
- Does it include auto-update logic?
- Does it include hidden telemetry?

## 4) Recommended first wave
Order for first review cycle:
1. LangGraph
2. SWE-agent-mini
3. OpenHands SDK subset
4. Continue patterns (read-only extraction)
5. Aider patterns
6. OpenClaw comparative review

Rationale:
- start with orchestration and eval primitives,
- then layer developer UX patterns,
- keep highest uncertainty source for late review.
