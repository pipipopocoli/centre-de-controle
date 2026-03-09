# ISSUE-CP-0065 - Responsive tablette

- Owner: leo
- Phase: Review
- Status: Done
- Source: ai_auto

## Objective
- Rendre le shell Cockpit fonctionnel sur largeur tablette, paysage et portrait.

## Done (Definition)
- [x] `Pixel Home` garde une vue scene prioritaire et un panneau operateur usable entre 1024 et 1366 px.
- [x] Les tabs secondaires passent en layout simple et scrollable sur tablette.
- [x] Les hypotheses desktop-only de largeur/hauteur sont reduites.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop/src/App.css
- /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop/src/App.tsx

## Risks
- Le shell tablette reste optimise usage operateur, pas parite visuelle stricte desktop.

## Evidence
- `npm --prefix /Users/oliviercloutier/Desktop/Cockpit/apps/cockpit-desktop run build`
- Breakpoints tablette dedies poses a `1366px`, `1100px`, `900px`.
