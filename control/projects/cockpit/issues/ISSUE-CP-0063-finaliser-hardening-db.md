# ISSUE-CP-0063 - Finaliser hardening DB

- Owner: victor
- Phase: Review
- Status: Done
- Source: ai_auto

## Objective
- Durcir la DB runtime SQLite sans changer le schema produit.

## Done (Definition)
- [x] Ouverture runtime DB centralisee dans `storage.rs`.
- [x] Pragmas appliques a chaque ouverture (`WAL`, `NORMAL`, `foreign_keys=ON`, `busy_timeout`, `temp_store=MEMORY`).
- [x] Index runtime poses pour `events`, `chat_messages`, `approval_requests`.
- [x] Integrity check disponible pour les tests et le bootstrap de verification.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/crates/cockpit-core/src/storage.rs

## Risks
- Toute future ouverture directe hors helper peut reintroduire du drift SQLite.

## Evidence
- `cargo check --manifest-path /Users/oliviercloutier/Desktop/Cockpit/crates/cockpit-core/Cargo.toml`
- `cargo test --manifest-path /Users/oliviercloutier/Desktop/Cockpit/crates/cockpit-core/Cargo.toml storage::tests::runtime_db_integrity_check_passes_after_scaffold`
