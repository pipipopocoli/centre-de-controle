# ISSUE-CP-0066 - Audit accessibilite WCAG

- Owner: leo
- Phase: Review
- Status: Done
- Source: ai_auto

## Objective
- Faire un audit WCAG 2.2 AA pragmatique sur les flows operateur critiques et corriger les ecarts obligatoires.

## Done (Definition)
- [x] Focus visible ajoute sur controles, tabs, inputs, selects et zones scrollables focusables.
- [x] Labels explicites/ARIA ajoutes aux zones placeholder-only et aux boutons icone-only critiques.
- [x] Pack d audit courant cree dans `docs/releases`.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop/src/App.tsx
- /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop/src/App.css
- /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WCAG_AUDIT_MATRIX_2026-03-09.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WCAG_FIXED_NOW_2026-03-09.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WCAG_DEFERRED_2026-03-09.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/releases/WCAG_KEYBOARD_CHECKLIST_2026-03-09.md

## Risks
- Un audit lecteur d ecran complet macOS reste a faire en verification manuelle.

## Evidence
- `npm --prefix /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop run lint`
- Parcours clavier manuel documente dans le pack WCAG.
