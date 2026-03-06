# Status Report PDF (dual-root)

Ce document décrit le pipeline de rapport PDF d'état projet (repo + AppSupport).

## Commande recommandée

```bash
./.venv/bin/python scripts/export_status_pdf.py \
  --project-id cockpit \
  --scope dual-root \
  --out "./COCKPIT_STATUS_2026-03-02.pdf" \
  --language fr
```

## Ce que le script produit

- Snapshot déterministe:
  - `STATE.md`, `ROADMAP.md`, `DECISIONS.md` (repo + AppSupport)
  - `git status -sb`, `git diff --name-only`, `git diff --stat`, `git log --oneline -5`
  - 8 checks Wave19/Wave18 + smoke check `scripts/render_presentation_pdf.py`
- Détection findings:
  - bugs (P0/P1)
  - éléments manquants
  - statut global `healthy|degraded|blocked`
- PDF final avec sections:
  - Executive Summary
  - Où on en est
  - Ce qui fonctionne
  - Ce qui bug
  - Ce qui manque
  - Prochaines étapes
  - Registre des risques
  - Annexe evidence

## Ligne stable de sortie

Le script imprime toujours:

```text
StatusPdfSummary project_id=... scope=... overall=... bugs=... missing=... out=...
```

## Notes

- Si `--out` existe déjà, le script écrit un fichier suffixé UTC (`_<timestamp>Z.pdf`).
- Le rendu PDF utilise `PySide6` (`QTextDocument` + `QPrinter`).
