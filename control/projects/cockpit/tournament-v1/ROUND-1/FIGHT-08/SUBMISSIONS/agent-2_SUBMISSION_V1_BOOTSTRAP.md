# agent-2 Submission V1 Bootstrap (R16 F08 - Pulse)

## Objective
- Stabiliser Cockpit V1 (UI+docs+setup+MCP) avec livrables verifiables et reversibles.

## Scope in/out
- Scope in:
- Hygiene etat projet (STATE.md vivant, definition claire des phases Plan/Implement/Test/Review/Ship).
- Workflow court et testable issue -> PR -> test -> review -> ship.
- Runbook court et QA gates verifiables pour eviter le drift process.
- Scope out:
- Refonte produit large.
- Changements hors F08.
- Features non testables ou non reversibles.

## Architecture/workflow summary
- Cadence operationnelle:
- 1 issue locale = 1 tache, owner unique.
- 1 PR = 1 livraison petite, testable, reversible.
- WIP max = 5 items In Progress.
- Escalade blocker > 60 min avec 2 options + 1 reco.
- Flux de livraison:
- Plan: cadrer objectif/scope/risques/decisions.
- Implement: coder et brancher.
- Test: verifier scenarios et gates.
- Review: nettoyer et rendre merge-ready.
- Ship: merge et suivi.

## Changelog vs previous version
- V1 bootstrap initial.
- Aucune version precedente disponible.

## Imported opponent ideas (accepted/rejected/deferred)
- Deferred:
- Deferred (Phase B, en attente bootstrap adverse).
- No accepted ideas yet.
- No rejected ideas yet.

## Risk register
- Risk: schema drift entre etat attendu et etat reel.
- Mitigation: gate de structure obligatoire + mise a jour STATE/DECISIONS.
- Risk: blocage inter-agent si bootstrap adverse absent.
- Mitigation: stop explicite apres Phase A + signal blocker canonique.
- Risk: process drift (WIP, owner, DoD non respectes).
- Mitigation: checklist DoD + QA gates avant publication.

## Test and QA gates
- Gate 1 (file presence):
- `test -f /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-08/SUBMISSIONS/agent-2_SUBMISSION_V1_BOOTSTRAP.md`
- Gate 2 (ASCII only):
- `rg -n '[^\x00-\x7F]' /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-08/SUBMISSIONS/agent-2_SUBMISSION_V1_BOOTSTRAP.md || true`
- Gate 3 (required sections present):
- Verify all 10 section headers exist exactly once.
- Gate 4 (footer contract):
- Verify end contains `Now:`, `Next:`, `Blockers:`.
- Gate 5 (phase gate):
- If opponent bootstrap missing, do not write FINAL.

## DoD checklist
- [x] Output path conforme.
- [x] Structure des 10 sections presente.
- [x] Risques majeurs identifies avec mitigation.
- [x] Strategie de test/QA explicite et verifiable.
- [x] Plan reversible (petite livraison, rollback par revert).
- [ ] Phase B absorption completee (conditionnelle au fichier adverse).

## Next round strategy
- Importer au moins 3 idees adverses des que le bootstrap adverse est disponible.
- Rejeter au moins 1 idee faible de cette version avec raison technique claire.
- Garder la prochaine iteration petite, testable, reversible.
- Prioriser les gains qui reduisent risque operationnel et temps de validation.

## Now/Next/Blockers
- Now: Bootstrap V1 de @agent-2 publie avec sections et QA gates.
- Next: Attendre le bootstrap adverse puis executer Phase B et produire FINAL.
- Blockers: BLOCKER: missing file /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-08/SUBMISSIONS/agent-15_SUBMISSION_V1_BOOTSTRAP.md
