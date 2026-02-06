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
