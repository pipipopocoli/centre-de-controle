# WAVE11 Push Manifest - 2026-02-23

## Timestamp
- UTC: 2026-02-22T18:34:26Z

## Branch (before snapshot branch create)
- main

## Runtime roots
- AppSupport: /Users/oliviercloutier/Library/Application Support/Cockpit/projects
- Repo: /Users/oliviercloutier/Desktop/Cockpit/control/projects

## Vulgarisation freshness
- 2026-02-23 01:34:14 /Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/vulgarisation/index.html
- 2026-02-23 01:34:14 /Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/vulgarisation/snapshot.json
- 2026-02-21 00:21:10 /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/vulgarisation/index.html
- 2026-02-21 00:21:10 /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/vulgarisation/snapshot.json

## Changed files (git status --short)
 M AGENTS.md
 M app/data/model.py
 M app/data/store.py
 M app/main.py
 M app/services/auto_mode.py
 M app/services/chat_parser.py
 M app/services/cost_telemetry.py
 M app/services/execution_router.py
 M app/services/memory_index.py
 M app/services/project_bible.py
 M app/services/project_pilotage.py
 M app/ui/agents_grid.py
 M app/ui/chatroom.py
 M app/ui/main_window.py
 M app/ui/project_bible.py
 M app/ui/project_pilotage.py
 M app/ui/project_timeline.py
 M app/ui/sidebar.py
 M app/ui/theme.qss
 M control/projects/cockpit/ROADMAP.md
 M control/projects/cockpit/STATE.md
 M control/projects/cockpit/issues/ISSUE-CP-0031-wave05-cost-telemetry-cad.md
 M control/projects/cockpit/settings.json
 M docs/PACKAGING.md
 M docs/RUNBOOK.md
 M docs/reports/BACKLOG_CLEANUP_V2.md
 M docs/reports/BACKLOG_TOURNAMENT_PRESERVATION.md
 M docs/reports/CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md
 M scripts/auto_mode.py
 M scripts/auto_mode_core.py
 M scripts/auto_mode_healthcheck.py
 M tests/verify_auto_mode.py
 M tests/verify_cost_telemetry.py
 M tests/verify_execution_router.py
 M tests/verify_memory_index.py
 M tests/verify_project_bible.py
?? "Centre de controle.spec"
?? "Cockpit V2 \342\200\224 Projet Technique Complet.pdf"
?? Cockpit_V2_Charter.pdf
?? Cockpit_V2_Le_Grand_Merge_Master_Plan.pdf
?? Cockpit_V2_MegaPrompt_Clems.pdf
?? Cockpit_V2_Projet_Technique_Complet.pdf
?? Cockpit_V2_Tournament_Pack.pdf
?? README.md
?? agents/nova.md
?? app/cockpit/
?? app/services/agent_registry.py
?? app/services/antigravity_runner.py
?? app/services/codex_runner.py
?? app/services/eval_audit.py
?? app/services/eval_policy.py
?? app/services/eval_registry.py
?? app/services/gatekeeper.py
?? app/services/ollama_runner.py
?? app/services/reliability_core.py
?? app/services/session_state.py
?? app/services/skills_catalog.py
?? app/services/skills_governance.py
?? app/services/skills_installer.py
?? app/services/skills_policy.py
?? app/services/task_matcher.py
?? app/services/timeline_feed.py
?? app/ui/assets/
?? assets/
?? control/examples/reply_to_inbox.py
?? control/examples/report_slo_cost_qa.py
?? control/examples/report_ui_qa.py
?? control/examples/start_mission.py
?? control/projects/_archive/
?? control/projects/cockpit/CHECKPOINT_GROS_PUSH_2026-02-13.md
?? control/projects/cockpit/DECISIONS.md
?? control/projects/cockpit/PAPER_PLAN_NEXT_STEPS_CP01_V2.md
?? control/projects/cockpit/PAPER_PLAN_WAVE04_PARALLELIZATION_MAX_2026-02-19.md
?? control/projects/cockpit/PLAN_PAPER_SKILLS_OPS_MEMORY_V2.md
?? control/projects/cockpit/RELEASE_SNAPSHOT_2026-02-13.md
?? control/projects/cockpit/agents/
?? control/projects/cockpit/issues/ISSUE-CP-0001-skills-catalog-fetch-cache-fallback.md
?? control/projects/cockpit/issues/ISSUE-CP-0002-policy-engine-curated-fail-open.md
?? control/projects/cockpit/issues/ISSUE-CP-0003-installer-wrapper-idempotence.md
?? control/projects/cockpit/issues/ISSUE-CP-0011-ui-skills-ops-panel.md
?? control/projects/cockpit/issues/ISSUE-CP-0012-ui-sync-now-feedback.md
?? control/projects/cockpit/issues/ISSUE-CP-0013-ui-observability-badges.md
?? control/projects/cockpit/issues/ISSUE-CP-0014-ui-fail-open-network-down-states.md
?? control/projects/cockpit/issues/ISSUE-CP-0015-ui-integrate-html-docs.md
?? control/projects/cockpit/issues/ISSUE-CP-0016-victor-l3-fight15-dual-stage.md
?? control/projects/cockpit/issues/ISSUE-CP-0021-wave04-control-loop-cadence.md
?? control/projects/cockpit/issues/ISSUE-CP-0022-wave04-ui-ship-lock.md
?? control/projects/cockpit/issues/ISSUE-CP-0023-wave04-backend-contract-lock.md
?? control/projects/cockpit/issues/ISSUE-CP-0024-wave04-cleanup-canonicalization.md
?? control/projects/cockpit/issues/ISSUE-CP-0025-wave04-dispatch-pack-and-operator-packet.md
?? control/projects/cockpit/issues/ISSUE-CP-0026-wave05-agent-registry-runtime.md
?? control/projects/cockpit/issues/ISSUE-CP-0027-wave05-platform-mapping-from-registry.md
?? control/projects/cockpit/issues/ISSUE-CP-0028-wave05-task-scoring-engine.md
?? control/projects/cockpit/issues/ISSUE-CP-0029-wave05-dispatch-backpressure.md
?? control/projects/cockpit/issues/ISSUE-CP-0030-wave05-router-tiered-fallback.md
?? control/projects/cockpit/issues/ISSUE-CP-0032-wave05-slo-gates.md
?? control/projects/cockpit/issues/ISSUE-CP-0033-wave06-nova-global-l1.md
?? control/projects/cockpit/issues/ISSUE-CP-0034-wave07-ui-polish.md
?? control/projects/cockpit/issues/ISSUE-CP-0035-wave09-dual-root-control-cadence.md
?? control/projects/cockpit/issues/ISSUE-CP-0036-wave09-healthcheck-contract-hardening.md
?? control/projects/cockpit/issues/ISSUE-CP-0037-wave09-pilotage-control-badges.md
?? control/projects/cockpit/issues/ISSUE-CP-0038-wave09-advisory-closeout-ledger.md
?? control/projects/cockpit/issues/ISSUE-CP-0039-wave10-chat-incremental-scroll-lock.md
?? control/projects/cockpit/issues/ISSUE-CP-0040-wave10-refresh-decoupling-performance.md
?? control/projects/cockpit/issues/ISSUE-CP-0041-wave10-ui-click-context-routing.md
?? control/projects/cockpit/issues/ISSUE-CP-0042-wave10-vulgarisation-clean-simple-tech.md
?? control/projects/cockpit/issues/ISSUE-CP-0043-wave10-throughput-burst-governance.md
?? control/projects/cockpit/issues/ISSUE_MAP_WAVE04_CP002X.md
?? control/projects/cockpit/issues/ISSUE_MAP_WAVE05_CP003X.md
?? control/projects/cockpit/issues/ISSUE_MAP_WAVE09_CP0035_CP0038.md
?? control/projects/cockpit/missions/
?? control/projects/cockpit/roadmap.yml
?? control/projects/cockpit/runs/NEXT_WAVE_INTAKE_OPEN_2026-02-19.md
?? control/projects/cockpit/runs/NOVA_CREATIVE_SCIENCE_KICKOFF_2026-02-19.md
?? control/projects/cockpit/runs/V2_WAVE04_DISPATCH_2026-02-19.md
?? control/projects/cockpit/runs/V2_WAVE05_DISPATCH_2026-02-19.md
?? control/projects/cockpit/runs/V2_WAVE07_DISPATCH_2026-02-19.md
?? control/projects/cockpit/runs/V2_WAVE08_DISPATCH_2026-02-20.md
?? control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md
?? control/projects/cockpit/runs/V2_WAVE10_DISPATCH_2026-02-22.md
?? control/projects/cockpit/runs/V2_WAVE11_DISPATCH_2026-02-23.md
?? control/projects/cockpit/runs/WAVE04_GATE_CHECKLIST_2026-02-19.md
?? control/projects/cockpit/runs/WAVE04_OPERATOR_PACKET_DRAFT_2026-02-19.md
?? control/projects/cockpit/runs/WAVE06_BACKEND_GATE_RECHECK_2026-02-19T1730Z.md
?? control/projects/cockpit/runs/WAVE06_BACKEND_SHIP_READINESS_2026-02-19T1728Z.md
?? control/projects/cockpit/runs/WAVE06_BACKEND_STATUS_2026-02-19T1717Z.md
?? control/projects/cockpit/runs/WAVE06_BACKEND_STATUS_2026-02-19T1727Z.md
?? control/projects/cockpit/runs/WAVE06_CLOSEOUT_2026-02-19.md
?? control/projects/cockpit/runs/WAVE07_BACKEND_HARDENING_2026-02-19T1803Z.md
?? control/projects/cockpit/runs/WAVE07_NOVA_ADVISORY_CHECKPOINT_2026-02-19T1753Z.md
?? control/projects/cockpit/runs/WAVE07_QUEUE_RECOVERY_2026-02-20T1730Z.md
?? control/projects/cockpit/runs/WAVE08_CLOSEOUT_FULL_2026-02-20.md
?? control/projects/cockpit/runs/WAVE09_DECISION_2026-02-20T2148Z.md
?? control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md
?? control/projects/cockpit/runs/WAVE09_LEO_DECISION_2026-02-20T2150Z.md
?? control/projects/cockpit/runs/WAVE09_LIVE_APP_LOCK_2026-02-21.md
?? control/projects/cockpit/runs/WAVE09_LIVE_APP_LOCK_APPLIED_2026-02-21.md
?? control/projects/cockpit/runs/WAVE09_NEXT_SYNC_2026-02-22T1542Z.md
?? control/projects/cockpit/runs/WAVE09_NOVA_PLAN_KICKOFF_2026-02-20T2138Z.md
?? control/projects/cockpit/runs/WAVE09_PRECHECK_2026-02-20.md
?? control/projects/cockpit/runs/WAVE09_RUNTIME_FINAL_LOCK_2026-02-20T2221Z.md
?? control/projects/cockpit/runs/WAVE11_PUSH_MANIFEST_2026-02-23.md
?? control/projects/cockpit/runs/control_snapshot_2026-02-18.md
?? control/projects/cockpit/runs/control_snapshot_2026-02-19.md
?? control/projects/cockpit/runs/control_snapshot_wave04_t0_2026-02-19.md
?? control/projects/cockpit/runs/reliability/
?? control/projects/cockpit/runs/slo_verdict_latest.json
?? control/projects/cockpit/tournament-v1/
?? control/projects/cockpit/tournament-v2/
?? control/projects/cockpit/vulgarisation/
?? control/projects/demo/agents/nova/
?? control/projects/demo/agents/registry.json
?? control/projects/demo/runs/
?? control/projects/demo/vulgarisation/
?? control/ui_session.json
?? docs/COCKPIT_PRESENTATION.pdf
?? docs/cockpit_v2_roadmap.html
?? docs/cockpit_v2_whitepaper.html
?? docs/generate_pdf.py
?? docs/reports/CP0037_QA_EVIDENCE_PACK_2026-02-21.md
?? docs/reports/CP0037_QA_SCENARIO_MATRIX_2026-02-21.md
?? docs/reports/CP01_SLO_COST_EVIDENCE_2026-02-19.md
?? docs/reports/CP01_TIMELINE_EVIDENCE_2026-02-20.md
?? docs/reports/CP01_UI_WAVE07_EVIDENCE.md
?? docs/reports/CP01_VULGARISATION_UPGRADE_WAVE07.md
?? docs/reports/QA_CLOSEOUT_WAVE06.md
?? docs/reports/WAVE04_CLEANUP_DECISION_DRAFT_2026-02-19.md
?? docs/reports/WAVE07_QUEUE_DEDUPE_PROOF.md
?? docs/reports/agent-2/
?? docs/reports/cp01-ui-qa/WAVE06_UI_EVIDENCE_MAPPING.md
?? docs/reports/cp01-ui-qa/evidence/
?? docs/reports/v3.7/
?? docs/research/
?? repo/
?? scripts/capture_degraded.py
?? scripts/dedupe_queue.py
?? scripts/generate_pilotage_evidence.py
?? scripts/generate_s5_eval_reports.py
?? scripts/generate_timeline_evidence.py
?? scripts/packaging/assets/
?? scripts/packaging/build_icon_icns.sh
?? scripts/packaging/generate_tree_icon.py
?? scripts/packaging/install_dev_live_launcher.sh
?? scripts/release/
?? scripts/reliability_recovery.py
?? scripts/render_presentation_pdf.py
?? scripts/reply_as_leo_wave06.py
?? scripts/reply_as_leo_wave07.py
?? scripts/reply_wave07_status.py
?? scripts/report_cp0037_agent6.py
?? scripts/report_cp0037_agent7.py
?? scripts/report_mission_leo.py
?? scripts/report_wave06_to_clems.py
?? scripts/report_wave09_leo.py
?? scripts/skills_install_wrapper.py
?? scripts/update_leo_state.py
?? scripts/verify_mega_merge_lock.py
?? scripts/verify_ui_polish.py
?? site/
?? tests/repro_atomic_write.py
?? tests/repro_skills_gates.py
?? tests/repro_task_cap.py
?? tests/verify_agent3_lifecycle_report.py
?? tests/verify_agent_registry.py
?? tests/verify_antigravity_runner.py
?? tests/verify_auto_mode_healthcheck.py
?? tests/verify_codex_runner.py
?? tests/verify_eval_harness.py
?? tests/verify_gatekeeper_eval_integration.py
?? tests/verify_hybrid_timeline.py
?? tests/verify_queue_dedupe.py
?? tests/verify_reliability_core.py
?? tests/verify_run_loop_kpi.py
?? tests/verify_skills_catalog.py
?? tests/verify_skills_governance.py
?? tests/verify_skills_installer.py
?? tests/verify_skills_ops_panel.py
?? tests/verify_skills_policy.py
?? tests/verify_slo_cost.py
?? tests/verify_timeline_deterministic.py
?? tests/verify_timeline_feed.py
?? tests/verify_vulgarisation_accessibility.py
?? tests/verify_vulgarisation_comprehension.py
?? tests/verify_vulgarisation_contract.py
?? tests/verify_wave05_dispatch.py
?? tests/verify_wave06_nova.py
?? tests/verify_wave07_control_gates.py
?? tests/verify_wave07_queue_recovery.py
?? tests/verify_wave09_dual_root_cadence.py
?? tests/verify_wave10_runtime_lane.py
?? tools/

## Smoke gate results
- verify_project_bible: PASS
- verify_vulgarisation_contract: PASS
- verify_hybrid_timeline: PASS
- verify_ui_polish: PASS

## Runtime gate snapshot
- repo healthcheck: healthy
- appsupport healthcheck: healthy
