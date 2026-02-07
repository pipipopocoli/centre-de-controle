# Decisions

## 2026-02-06 - ADR-001 Python >=3.11
- Status: Accepted
- Context: MCP requiert >=3.10 et l'environnement actuel manque d'un standard clair.
- Decision: Cibler Python >=3.11 (3.12 supporte).
- Rationale: Simplifie l'outillage, beneficie des ameliorations de 3.11, evite les divergences.
- Consequences: Update des guides d'installation et tooling; certains contributeurs doivent upgrader.
- Owners: Clems, Victor, Leo
- References: ROADMAP.md

## 2026-02-06 - ADR-002 Phases UI + schema state.json
- Status: Accepted
- Context: Besoin d'un vocabulaire de phases stable et d'un schema canonique pour l'etat.
- Decision: Phases UI officielles = Plan, Implement, Test, Review, Ship. Schema state.json = engine (CDX/AG), phase (string), percent, eta_minutes, heartbeat, status, blockers.
- Rationale: Assure coherence UI/MCP et facilite la migration et le reporting.
- Consequences: Migration des etats existants et mise a jour des specs et docs.
- Owners: Clems, Victor, Leo
- References: STATE.md

## 2026-02-06 - ADR-003 UI direction (Paper Ops) + fonts V1
- Status: Accepted
- Context: L'UI actuelle est "fonctionnelle mais laide" et on veut une direction stable (pas de churn) avant l'implementation.
- Decision: UI direction V1 = Paper Ops. Fonts V1 = pas de fonts bundlees (fallback system clean).
- Rationale: Donne une hierarchie forte et un look intentionnel, sans alourdir V1 avec de la gestion d'assets/fonts.
- Consequences: Phase 2 UI = QSS tokens + layout + screenshot; bundling fonts reste une option V2.
- Owners: Clems, Leo
- References: docs/ui-research.md, control/projects/demo/issues/ISSUE-0006-ui-redesign-v1.md

## 2026-02-06 - ADR-004 Version stamp + dev QSS reload
- Status: Accepted
- Context: Risque eleve de lancer une vieille version (dist/ancienne branche) et perdre du temps a debugguer des fantomes.
- Decision: Afficher un version stamp (branch@sha[*]) dans le titre + sidebar footer. Hot reload du style via app/ui/theme.qss en dev.
- Rationale: Rend la version visible immediatement, et permet d'iterer sur le style sans relancer l'app.
- Consequences: Pour les changements Python, restart reste necessaire; le QSS se reload a la sauvegarde.
- Owners: Clems, Victor
- References: control/projects/demo/issues/ISSUE-0007-version-stamp-dev-reload.md

## 2026-02-06 - ADR-005 Run requests handshake (agent loop e2e)
- Status: Accepted
- Context: Besoin d'un handshake minimal pour relier un ping a une action agent (AG/MCP) sans scheduler.
- Decision: Emission de run requests en NDJSON local: control/projects/<id>/runs/requests.ndjson. Chaque mention cree une entree avec request_id, project_id, agent_id (target), status=queued, source=mention, created_at, et le message source.
- Rationale: Local-first, auditable, simple a consommer par un agent externe.
- Consequences: Le log peut grossir; rotation/compaction a faire en V3.
- Owners: Clems, Victor
- References: control/projects/demo/issues/ISSUE-0010-agent-loop-e2e-v2.md

## 2026-02-06 - ADR-006 Data dir fallback for packaging
- Status: Accepted
- Context: Packaged app cannot rely on repo-local control/projects path.
- Decision: Data dir precedence: COCKPIT_DATA_DIR -> repo control/projects (if present) -> ~/Library/Application Support/Cockpit/projects.
- Rationale: Local-first and stable path for .app while preserving dev workflow.
- Consequences: Packaged builds need QA for data path and permissions.
- Owners: Clems, Victor
- References: control/projects/demo/issues/ISSUE-0011-packaging-research-v2.md, docs/PACKAGING.md

## 2026-02-07 - ADR-007 Clems auto-reply + personas split
- Status: Accepted
- Context: Operator needs a primary assistant response in chat and clearer next steps.
- Decision: Clems auto-replies to operator messages; personas moved to agents/ files; roadmap shows Phase/Objective/Next.
- Rationale: Improves usability and reduces confusion about next actions.
- Consequences: Must avoid reply loops; reminders kept minimal.
- Owners: Clems, Victor, Leo
- References: control/projects/demo/issues/ISSUE-0012-clems-autoreply-v2.md

## 2026-02-07 - ADR-008 Parallel delegation via agent-N specialists
- Status: Accepted
- Context: Two leads (Victor/Leo) must work in parallel and be able to delegate to extra specialists without name chaos.
- Decision: Specialists are named `agent-<number>` (agent-1, agent-2, ...). Mentions allow only @clems/@victor/@leo + @agent-<number>. Mention creates a run request NDJSON even if the agent is not in the roster yet (no auto-create).
- Rationale: Simple convention, low collisions, auditable run requests, supports parallel work.
- Consequences: Specialists appear in the grid only when they post state; gitignore hides agent-N directories by default.
- Owners: Clems, Victor, Leo
- References: control/projects/demo/issues/ISSUE-0014-parallel-delegation-v2.md

## 2026-02-07 - ADR-009 V5 Brain Manager + Project Intake
- Status: Accepted
- Context: Need a full orchestrator to link existing repos, run intake, ask questions, and generate plans/issues.
- Decision: Add Brain Manager (brain_manager.py) with intake, question builder, task planner, and issue creation.
- Rationale: Enables consistent project onboarding and delegation at scale.
- Consequences: Requires UI wiring for project intake and lightweight scanning guardrails.
- Owners: Clems, Victor, Leo
- References: ROADMAP.md
