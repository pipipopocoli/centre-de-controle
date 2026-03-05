# Wave20R A9 Backlog

- Mission: Rust llm-profile/delegation/roadmap API implementation (mandatory design tickets)
- Scope allowlist: crates/cockpit-core/src/app.rs, crates/cockpit-core/src/models.rs, crates/cockpit-core/src/orchestrator.rs, crates/cockpit-core/src/chat.rs, crates/cockpit-core/src/openrouter.rs
- Source trackers: docs/swarm_results/wave1_p0p1_tracker.md, docs/swarm_results/wave2_p2_tracker.md, docs/swarm_results/wave2_p3_tracker.md, docs/swarm_results/wave20_unassigned_backlog.md
- Initial rows: 5

| issue_id | source | severity | file | status_before | action | evidence_command | evidence_result | reason_code | note |
|---|---|---|---|---|---|---|---|---|---|
| `ISSUE-W20R-A9-001` | `wave20r_design` | `P1` | `crates/cockpit-core/src/models.rs` | `open` | `done` | `cargo check --manifest-path crates/cockpit-core/Cargo.toml` | `check passed: LlmProfile model defined with LegacyProviderMapping, AgentRecord updated with optional llm_profile field` | `` | Define llm-profile Rust model and backward migration mapping fields |
| `ISSUE-W20R-A9-002` | `wave20r_design` | `P1` | `crates/cockpit-core/src/app.rs` | `open` | `done` | `cargo check --manifest-path crates/cockpit-core/Cargo.toml` | `check passed: get_llm_profile and put_llm_profile handlers implemented with OpenRouter normalization` | `` | Add GET/PUT /v1/projects/{id}/llm-profile endpoints in local runtime |
| `ISSUE-W20R-A9-003` | `wave20r_design` | `P1` | `crates/cockpit-core/src/app.rs` | `open` | `done` | `cargo check --manifest-path crates/cockpit-core/Cargo.toml` | `check passed: post_roadmap_clems_draft endpoint with delegation validation` | `` | Add POST /v1/projects/{id}/roadmap/clems-draft endpoint contract |
| `ISSUE-W20R-A9-004` | `wave20r_design` | `P1` | `crates/cockpit-core/src/orchestrator.rs` | `open` | `done` | `cargo check --manifest-path crates/cockpit-core/Cargo.toml` | `check passed: validate_delegation and is_delegation_authorized functions added` | `` | Enforce hierarchical delegation metadata and L0->L1/L1->L2 policy guards |
| `ISSUE-W20R-A9-005` | `wave20r_design` | `P1` | `crates/cockpit-core/src/openrouter.rs` | `open` | `done` | `cargo check --manifest-path crates/cockpit-core/Cargo.toml` | `check passed: normalize_provider ensures OpenRouter-only, legacy providers mapped on read` | `` | Ensure OpenRouter-only execution path; map legacy providers on read then persist openrouter |
