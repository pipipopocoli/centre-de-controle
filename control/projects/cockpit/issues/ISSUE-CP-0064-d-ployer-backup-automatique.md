# ISSUE-CP-0064 - Deployer backup automatique

- Owner: victor
- Phase: Review
- Status: Done
- Source: ai_auto

## Objective
- Ajouter un backup avant operations risquees uniquement, sans scheduler continu.

## Done (Definition)
- [x] Helper backend de backup avant op risquee disponible.
- [x] `settings`, `roadmap`, `chat reset`, et taches `takeover` declenchent un snapshot avant mutation.
- [x] Archive `flappycock` exportee vers Google Drive avec manifest avant suppression locale.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/crates/cockpit-core/src/storage.rs
- /Users/oliviercloutier/Desktop/Cockpit/crates/cockpit-core/src/app.rs
- /Users/oliviercloutier/Library/CloudStorage/GoogleDrive-oliviier.cloutier@gmail.com/Mon disque/Cockpit/archive/live-project-removals/flappycock/20260309T070027Z/archive_manifest.md

## Risks
- Les mutations hors routes backend ne declenchent pas encore de backup pre-op.

## Evidence
- `GET /v1/projects` ne remonte plus `flappycock`.
- Archive verifiee sur Drive puis suppression locale de `control/projects/flappycock`.
