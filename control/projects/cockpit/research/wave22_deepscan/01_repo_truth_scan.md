# Wave22 Repo Truth Scan

## Live Surfaces

| Surface | Root | Files | Key Findings |
|---|---|---:|---:|
| `desktop_tauri` | `apps/cockpit-desktop` | 131 | 2 |
| `rust_core` | `crates/cockpit-core` | 12 | 25 |
| `python_app` | `app` | 152 | 29 |
| `python_server` | `server` | 26 | 5 |
| `android` | `android` | 6 | 4 |
| `scripts` | `scripts` | 79 | 23 |
| `docs_active` | `docs` | 27 | 25 |
| `control_project` | `control/projects/cockpit` | 228 | 400 |

## Notes

- `control_project` / `stale_api_refs`: 80 hit(s)
  - `control/projects/cockpit/DECISIONS.md:233` - - Decision: Add OpenRouter-backed runtime endpoints (`llm-profile`, `chat/agentic-turn`, `voice/transcribe`, `pixel-feed`), wire desktop controls (`Model Routing`, `Vocal`, `Scène`, `Pixel View`), and bootstrap Android m
  - `control/projects/cockpit/research/wave22_deepscan/07_optimization_backlog.md:5` - - Audit and correct stale endpoint docs that still advertise `chat/agentic-turn` and `wizard-live` in active surfaces.
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:306` - "snippet": "f\"/v1/projects/{urllib.parse.quote(project_id, safe='')}/chat/agentic-turn\","
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:319` - "snippet": "Route(\"/v1/projects/{project_id:str}/chat/agentic-turn\", post_agentic_turn, methods=[\"POST\"]),"
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:324` - "snippet": "Route(\"/v1/projects/{project_id:str}/wizard-live/start\", wizard_start, methods=[\"POST\"]),"
- `control_project` / `legacy_runtime`: 80 hit(s)
  - `control/projects/cockpit/STATE.md:31` - - Active docs and code still contain legacy naming and stale endpoint references that can confuse implementation.
  - `control/projects/cockpit/DECISIONS.md:53` - - Consequences: `cockpit.spec` and `cockpit_v5.spec` are legacy/non-canonical references; `venv/` is fallback-only; root `Cockpit_V2_*.pdf` files are archive references, not primary operational source-of-truth.
  - `control/projects/cockpit/DECISIONS.md:217` - - Consequences: Introduces `server/` backend foundation, auth/JWT/RBAC contracts, event envelope stream, and device registration for Android push; legacy local-file mode moves behind migration/cutover gates.
  - `control/projects/cockpit/DECISIONS.md:242` - - Decision: Lock active runtime execution to OpenRouter only. Keep legacy provider values only in normalization/migration adapters, and persist normalized provider as `openrouter`.
  - `control/projects/cockpit/DECISIONS.md:280` - - Consequences: `Overview` becomes read-only for project status, `Le Conseil` is the single action surface for greenfield/takeover flows, legacy settings keys are destroyed on save, and runtime diagnostics can now distin
- `control_project` / `legacy_naming`: 80 hit(s)
  - `control/projects/cockpit/RELEASE_SNAPSHOT_2026-02-13.md:6` - - Artifact: `dist/Centre de controle.app`
  - `control/projects/cockpit/RELEASE_SNAPSHOT_2026-02-13.md:16` - - Check A: launch packaged binary for 6 seconds (`dist/Centre de controle.app/Contents/MacOS/Centre de controle`)
  - `control/projects/cockpit/RELEASE_SNAPSHOT_2026-02-13.md:16` - - Check A: launch packaged binary for 6 seconds (`dist/Centre de controle.app/Contents/MacOS/Centre de controle`)
  - `control/projects/cockpit/roadmap.yml:2` - - Bootstrap Centre de controle UI
  - `control/projects/cockpit/DECISIONS.md:51` - - Decision: Lock cleanup canonicals to `Centre de controle.spec`, `.venv/`, and docs source-of-truth split as `docs/reports/` (ops evidence) plus `tournament-v1/` and `tournament-v2/` (tournament evidence). Keep tourname
- `control_project` / `demo_refs`: 80 hit(s)
  - `control/projects/cockpit/PLAN_PAPER_SKILLS_OPS_MEMORY_V2.md:52` - - Project id: `cockpit` only (no demo/evozina/motherload).
  - `control/projects/cockpit/STATE.md:32` - - Many tests and examples still lean on `demo`, which can hide live-project regressions.
  - `control/projects/cockpit/DECISIONS.md:259` - - Context: The desktop shell was mixing live work on `cockpit` with lingering `demo` project artifacts, and local issue files had split one functional problem into duplicate UI tickets.
  - `control/projects/cockpit/DECISIONS.md:260` - - Decision: Remove `control/projects/demo` from the active repo, keep `cockpit` as the only live project in the current operator flow, and consolidate the active shell recovery work onto `ISSUE-CP-0061` (Pixel Home) and
  - `control/projects/cockpit/DECISIONS.md:262` - - Consequences: `demo` stops surfacing in `/v1/projects`, active docs/scripts stop using it, and duplicate local issue drafts are superseded by the two canonical issues.
- `control_project` / `debt_markers`: 80 hit(s)
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:490` - "snippet": "\"debt_markers\": re.compile(r\"\\b(?:TODO|FIXME|HACK)\\b\"),"
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:490` - "snippet": "\"debt_markers\": re.compile(r\"\\b(?:TODO|FIXME|HACK)\\b\"),"
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:490` - "snippet": "\"debt_markers\": re.compile(r\"\\b(?:TODO|FIXME|HACK)\\b\"),"
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:495` - "snippet": "\"debt_markers\": re.compile(r\"\\b(?:TODO|FIXME|HACK)\\b\"),"
  - `control/projects/cockpit/research/wave22_deepscan/repo_audit.json:495` - "snippet": "\"debt_markers\": re.compile(r\"\\b(?:TODO|FIXME|HACK)\\b\"),"
- `python_app` / `legacy_runtime`: 28 hit(s)
  - `app/ui/project_pilotage.py:32` - from app.services.cost_telemetry import estimate_monthly_cad_from_path, legacy_monthly_cad_estimate
  - `app/ui/project_pilotage.py:440` - legacy_costs_path = project_dir / "vulgarisation" / "costs.json"
  - `app/ui/project_pilotage.py:441` - legacy_payload: dict | None = None
  - `app/ui/project_pilotage.py:442` - if legacy_costs_path.exists():
  - `app/ui/project_pilotage.py:444` - parsed = json.loads(_read_text(legacy_costs_path))
- `rust_core` / `legacy_runtime`: 16 hit(s)
  - `crates/cockpit-core/src/openrouter.rs:23` - /// Maps legacy provider codes to OpenRouter model identifiers.
  - `crates/cockpit-core/src/openrouter.rs:25` - /// ISSUE-W20R-A9-005: Legacy provider normalization
  - `crates/cockpit-core/src/openrouter.rs:26` - pub fn normalize_legacy_provider(provider: &str) -> String {
  - `crates/cockpit-core/src/models.rs:413` - pub legacy_mapping: Option<HashMap<String, String>>,
  - `crates/cockpit-core/src/models.rs:497` - legacy_mapping: Some(HashMap::new()),
- `docs_active` / `legacy_runtime`: 15 hit(s)
  - `docs/COCKPIT_RUNBOOK.md:31` - Archived legacy launchers stay historical only and are out of the daily operator path.
  - `docs/PACKAGING.md:1` - # Packaging (legacy Python app archived, Cockpit active)
  - `docs/PACKAGING.md:5` - - Legacy Python packaging is archived.
  - `docs/PACKAGING.md:19` - 2. Keep legacy app references for historical evidence only.
  - `docs/PACKAGING.md:20` - 3. If a legacy package script is used, mark the run as debug/manual.
- `rust_core` / `demo_refs`: 9 hit(s)
  - `crates/cockpit-core/src/storage.rs:301` - || matches!(project_id.as_str(), "demo" | "flappycock")
  - `crates/cockpit-core/src/storage.rs:1666` - fs::create_dir_all(root.join("demo")).expect("create demo project");
  - `crates/cockpit-core/src/storage.rs:1666` - fs::create_dir_all(root.join("demo")).expect("create demo project");
  - `crates/cockpit-core/src/storage.rs:1691` - let project_id = "demo";
  - `crates/cockpit-core/src/storage.rs:1716` - let project_id = "demo";
- `scripts` / `legacy_runtime`: 8 hit(s)
  - `scripts/auto_mode_healthcheck.py:189` - lifecycle_mode = "runtime_v3" if runtime_requests else "legacy_v1"
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:45` - "legacy_runtime": re.compile(r"legacy_|legacy\b", re.I),
- `docs_active` / `stale_api_refs`: 5 hit(s)
  - `docs/CLOUD_API_PROTOCOL.md:47` - - `POST /v1/projects/{id}/chat/agentic-turn`
  - `docs/CLOUD_API_PROTOCOL.md:49` - - `POST /v1/projects/{id}/wizard-live/start|run|stop`
  - `docs/WIZARD_LIVE.md:26` - - `POST /v1/projects/{id}/chat/agentic-turn` (`mode=chat|scene`)
  - `docs/OPENROUTER_SETUP.md:32` - 3. Chat turn: `POST /v1/projects/{id}/chat/agentic-turn`
  - `docs/PARITY_MATRIX_DESKTOP_ANDROID.md:15` - | Wizard live start/run/stop | Required | Required | `POST /wizard-live/start|run|stop` |
- `docs_active` / `legacy_naming`: 5 hit(s)
  - `docs/PACKAGING.md:1` - # Packaging (legacy Python app archived, Cockpit active)
  - `docs/PACKAGING.md:5` - - Legacy Python packaging is archived.
  - `docs/RUNBOOK.md:5` - - Archived reference only (legacy Python app path).
  - `docs/RUNBOOK.md:14` - Do not use legacy Python packaging for daily operations.
  - `docs/RUNBOOK.md:19` - ./launch_cockpit_legacy.sh
- `scripts` / `stale_api_refs`: 4 hit(s)
  - `scripts/wave22_repo_audit.py:43` - "stale_api_refs": re.compile(r"chat/agentic-turn|wizard-live/start|wizard-live/run|wizard-live/stop", re.I),
  - `scripts/wave22_repo_audit.py:43` - "stale_api_refs": re.compile(r"chat/agentic-turn|wizard-live/start|wizard-live/run|wizard-live/stop", re.I),
  - `scripts/wave22_repo_audit.py:43` - "stale_api_refs": re.compile(r"chat/agentic-turn|wizard-live/start|wizard-live/run|wizard-live/stop", re.I),
  - `scripts/wave22_repo_audit.py:43` - "stale_api_refs": re.compile(r"chat/agentic-turn|wizard-live/start|wizard-live/run|wizard-live/stop", re.I),
- `scripts` / `legacy_naming`: 4 hit(s)
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
  - `scripts/wave22_repo_audit.py:41` - "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
- `scripts` / `demo_refs`: 4 hit(s)
  - `scripts/wave22_repo_audit.py:42` - "demo_refs": re.compile(r"\bdemo\b|wizard-demo|ws-demo|rbac-demo|proj_demo", re.I),
  - `scripts/wave22_repo_audit.py:42` - "demo_refs": re.compile(r"\bdemo\b|wizard-demo|ws-demo|rbac-demo|proj_demo", re.I),
  - `scripts/wave22_repo_audit.py:42` - "demo_refs": re.compile(r"\bdemo\b|wizard-demo|ws-demo|rbac-demo|proj_demo", re.I),
  - `scripts/wave22_repo_audit.py:42` - "demo_refs": re.compile(r"\bdemo\b|wizard-demo|ws-demo|rbac-demo|proj_demo", re.I),
- `python_server` / `stale_api_refs`: 4 hit(s)
  - `server/main.py:993` - Route("/v1/projects/{project_id:str}/chat/agentic-turn", post_agentic_turn, methods=["POST"]),
  - `server/main.py:995` - Route("/v1/projects/{project_id:str}/wizard-live/start", wizard_start, methods=["POST"]),
  - `server/main.py:996` - Route("/v1/projects/{project_id:str}/wizard-live/run", wizard_run, methods=["POST"]),
  - `server/main.py:997` - Route("/v1/projects/{project_id:str}/wizard-live/stop", wizard_stop, methods=["POST"]),
- `android` / `stale_api_refs`: 4 hit(s)
  - `android/app/src/main/java/com/cockpit/mobile/network/CockpitApi.kt:18` - @POST("/v1/projects/{project_id}/chat/agentic-turn")
  - `android/app/src/main/java/com/cockpit/mobile/network/CockpitApi.kt:21` - @POST("/v1/projects/{project_id}/wizard-live/start")
  - `android/app/src/main/java/com/cockpit/mobile/network/CockpitApi.kt:24` - @POST("/v1/projects/{project_id}/wizard-live/run")
  - `android/app/src/main/java/com/cockpit/mobile/network/CockpitApi.kt:27` - @POST("/v1/projects/{project_id}/wizard-live/stop")
- `scripts` / `debt_markers`: 3 hit(s)
  - `scripts/wave22_repo_audit.py:44` - "debt_markers": re.compile(r"\b(?:TODO|FIXME|HACK)\b"),
  - `scripts/wave22_repo_audit.py:44` - "debt_markers": re.compile(r"\b(?:TODO|FIXME|HACK)\b"),
  - `scripts/wave22_repo_audit.py:44` - "debt_markers": re.compile(r"\b(?:TODO|FIXME|HACK)\b"),
- `desktop_tauri` / `legacy_runtime`: 2 hit(s)
  - `apps/cockpit-desktop/src/office/layout/layoutSerializer.ts:295` - * Migrate old layouts that use legacy tile types (TILE_FLOOR=1, WOOD_FLOOR=2, CARPET=3, DOORWAY=4)
  - `apps/cockpit-desktop/src/lib/cockpitClient.ts:264` - legacy_mapping?: Record<string, string>
- `python_server` / `legacy_runtime`: 1 hit(s)
  - `server/repository.py:324` - risks=["Legacy local-file drift"],
