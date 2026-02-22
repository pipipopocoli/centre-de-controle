# Wave07 Nova advisory checkpoint - 2026-02-19T1753Z

## Scope inputs
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md

## 60s brief

### On est ou
- Phase active: Ship, avec objectif officiel de close Wave06 puis ouvrir Wave07 hardening avec runtime control intact.
- Gates runtime restes verts: pending=0, queued=0, stale_gt24h=0, et suite Wave06 verte.

### On va ou
- Executer Wave07 sur 3 lanes: backend hardening (@victor), UI polish (@leo), advisory integration (@nova).
- Tenir cadence de publication 2h pour signal clair avant closeout Wave07.

### Pourquoi
- Le risque principal n est plus le build initial, mais la fiabilite contractuelle et la qualite de decision operateur.
- Les risques actifs (`dispatch divergence`, `false GO/HOLD`, `cost drift`) exigent recos evidence-first a chaque checkpoint.

### Comment
- Publier une synthese 60s + top 5 recos (action, risque, mitigation, owner, evidence path) dans chat status/report.
- Maintenir un `Guidance Ledger` dans memory Nova pour tracer `pending/accepted/rejected` via owner ack.

## Top 5 recommandations (checkpoint)

### R1 [P0]
- Action: verrouiller un template unique de brief 60s au debut de chaque checkpoint 2h.
- Risque: drift narratif entre STATE et ROADMAP, donc mauvais arbitre de priorites.
- Mitigation: bloc obligatoire `On est ou / On va ou / Pourquoi / Comment` dans chaque post Nova.
- Owner: @clems
- Evidence path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md

### R2 [P0]
- Action: ajouter un gate de confiance SLO base sur volume d echantillons latence.
- Risque: faux GO/HOLD si p95/p99 est calcule sur trop peu d echantillons.
- Mitigation: marquer la reco `confidence: low` tant que volume min n est pas atteint et bloquer `accepted`.
- Owner: @victor
- Evidence path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md

### R3 [P1]
- Action: mapper chaque risque STATE a un test ou artefact de preuve nomme.
- Risque: risques suivis en texte sans verification objective.
- Mitigation: table `risque -> test/artefact -> dernier resultat` dans le prochain packet Wave07.
- Owner: @victor
- Evidence path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md

### R4 [P1]
- Action: instaurer un SLA d ack owner pour chaque reco Nova (<= 1 cycle de 2h).
- Risque: recommandations restent `pending` trop longtemps et perdent impact operateur.
- Mitigation: si pas d ack sous 2h, remonter en `Open Loops` et reposter avec ping owner explicite.
- Owner: @clems
- Evidence path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/chat/threads/status.ndjson

### R5 [P2]
- Action: lier les recos Nova aux lanes Wave07 en sortie actionnable par owner.
- Risque: recos pertinentes mais non converties en actions lane A/B/C.
- Mitigation: chaque reco finit par `owner + next action + evidence path` dans le post checkpoint.
- Owner: @nova
- Evidence path: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md

## Checkpoint status
- Now: checkpoint advisory Wave07 publie avec top 5 et tracking ledger.
- Next: attendre ack owner et re-evaluer statuts `accepted/rejected` au prochain cycle 2h.
- Blockers: none.
