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
