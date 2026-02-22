# Nova creative_science_lead kickoff - 2026-02-19

## Mini map des ecarts
- Ecart 1: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md` est sur Wave06 lock en phase Ship, pendant que `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md` reste sequence Wave05.
- Ecart 2: `nova` existe dans `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/registry.json` mais `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md` etait absent.

## Brief 60s

### On est ou
- Phase `Ship`, objectif courant: verrouiller lane backend Wave06 (timeline deterministic + fallback Nova L1) dans `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`.
- Gates runtime actifs: `pending_stale_gt24h == 0`, `stale_heartbeats_gt1h <= 2`, `queued_runtime_requests <= 3`.

### On va ou
- Finaliser le packet readout Wave06 backend et maintenir recheck horaire de sante runtime avant handoff ship.
- Re-aligner narration operationnelle entre etat courant Wave06 et roadmap active Wave05 pour eviter le drift operateur.

### Pourquoi
- Sans alignement explicite, le runbook peut annoncer un GO/HOLD sur de mauvaises hypotheses de wave.
- Les risques actifs deja listes (dispatch divergence, faux verdict SLO, cost drift) demandent une lecture decisionnelle ultra claire.

### Comment
- Publier une couche `creative-science` courte: 5 recos prioritaires avec preuve, risque, mitigation, owner.
- Mettre `nova` en source de verite memoire projet pour ancrer les futurs readouts sur les memes references.

## Recommandations creative-science

### R1 [P0] - Aligner la narration Wave06 vs roadmap active
- Lien preuve: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`, `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- Risque: les owners pilotent avec deux versions du "now" et ouvrent un mauvais gate.
- Mitigation: ajouter une ligne de transition explicite "Wave05 sequence complete -> Wave06 backend lock active" dans le prochain packet de statut.
- Owner: @clems

### R2 [P0] - Rendre la gate story SLO/cost/dispatch lisible en 20 secondes
- Lien preuve: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`, `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md`
- Risque: faux GO/HOLD si l operateur lit seulement un signal partiel (ex: queue sans latence).
- Mitigation: standardiser une table unique `signal -> seuil -> verdict -> action` dans chaque readout ship.
- Owner: @victor

### R3 [P1] - Transformer les risques STATE en experiences mesurables
- Lien preuve: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- Risque: les risques restent descriptifs et ne deviennent jamais testables.
- Mitigation: associer chaque risque a un test nomme et une preuve run (ex: regression dispatch -> verify suite cible).
- Owner: @nova

### R4 [P1] - Sortir un readout deterministic avant handoff ship
- Lien preuve: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`, `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- Risque: handoff oral incomplet, puis rerun inutile pour reconstruire le contexte.
- Mitigation: paquet fixe 1 page: objective, gates, verdict GO/HOLD, delta risques, next owners.
- Owner: @clems

### R5 [P2] - Installer une cadence creative-science evidence-first
- Lien preuve: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md`, `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- Risque: recommandations trop abstraites et non liees a la realite runtime.
- Mitigation: cadence quotidienne 5 min avec check `STATE + ROADMAP + DECISIONS` puis update memoire `nova`.
- Owner: @nova

## Validation rapide
- Brief: 4 rubriques presentes (`On est ou`, `On va ou`, `Pourquoi`, `Comment`).
- Recos: 5 recos, chacune avec `Risque` + `Mitigation` + `Lien preuve`.
- Scope: aucune mutation de `STATE.md`, `ROADMAP.md`, `DECISIONS.md`.
