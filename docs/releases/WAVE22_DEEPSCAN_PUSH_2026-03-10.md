# Wave22 Deep Scan Push - 2026-03-10

## Shipped in this push
- Reproducible repo audit script
- Wave22 deepscan research pack
- 10 local issues for staged multi-agent execution
- 10 mission files aligned to the issue map
- STATE/DECISIONS updated for Wave22
- Active docs hygiene pass for live Cockpit operator flow

## Main findings
- Live path is desktop-first: `apps/cockpit-desktop` + `crates/cockpit-core`.
- Active docs still had legacy launcher references and stale examples; low-risk surface cleanup is included in this push.
- Repo still contains historical compatibility and archive material that must be classified, not mixed into live operator guidance.
- Wave22 active execution starts with 5 lanes only, even though 10 agents are assigned, to respect WIP <= 5.

## Current operating rule
- 10 agents assigned, 5 active lanes max, 5 queued
- `cockpit` remains the single live project
- Reliability first

## Verification
- `npm --prefix apps/cockpit-desktop run lint`
- `npm --prefix apps/cockpit-desktop run build`
- `npm --prefix apps/cockpit-desktop run tauri:build`
- `cargo check --manifest-path crates/cockpit-core/Cargo.toml`
- `cargo check --manifest-path apps/cockpit-desktop/src-tauri/Cargo.toml`
- `python3 -m compileall -q app server scripts control tests`
- `python3 tests/verify_cockpit_chat_runtime.py`
- `python3 tests/verify_cockpit_takeover_runtime.py`
- `python3 tests/verify_cockpit_voice_runtime.py`
- `python3 tests/verify_cockpit_skills_library_runtime.py`
