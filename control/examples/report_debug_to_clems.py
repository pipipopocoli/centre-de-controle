import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

try:
    from control.mcp_server import handle_post_message, handle_update_agent_state
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message, handle_update_agent_state


async def main():
    agent_id = "leo"
    project_id = "cockpit"

    msg = (
        "**@clems — Rapport debug Leo : Stream UI P0 + tes 3 bugs**\n\n"
        "Voici le détail complet de ce que j'ai touché pendant cette session.\n\n"
        "---\n\n"
        "## Session 1 : Stream UI P0 (lisibilité opérationnelle)\n\n"
        "### Fichiers modifiés :\n\n"
        "**1. `app/ui/agents_grid.py`**\n"
        "- `_status_label()` : ajout d'emoji devant chaque statut :\n"
        "  - `⚡ En action` (was `En action`)\n"
        "  - `⏳ Attente réponse` (was `Attente reponse`)\n"
        "  - `🔴 Bloqué` (was `Bloque`)\n"
        "  - `💤 Repos` (was `Repos`)\n"
        "- `AgentCard.__init__()` :\n"
        "  - Ajout property `status-stripe` sur le QFrame → drive une bordure gauche 4px via QSS\n"
        "  - Ajout micro-header `MISSION` (QLabel objectName=`agentTaskHeader`) au-dessus du task text\n"
        "  - `technical_status` caché quand `status_key == 'rest'`\n"
        "  - Margins ajustées : `(14,10,12,10)` spacing `6` (was `(12,12,12,12)` spacing `8`)\n\n"
        "**2. `app/ui/sidebar.py`**\n"
        "- `RuntimeContextPanel` refait :\n"
        "  - **Avant** : 3 QLabels (`app_stamp`, `repo_head`, `project_context`) + bouton `Rebuild app`\n"
        "  - **Après** : 2 QLabels (`project_title` bold + `info_line` monospace `stamp:…|head:…`) — plus de rebuild button\n"
        "  - Warning mismatch : `⚠️ Mismatch: app X ≠ repo Y` au lieu de `Build mismatch: running X, repo Y`\n"
        "  - ⚠️ **BREAKING** : `self.app_stamp`, `self.repo_head`, `self.project_context` n'existent plus. "
        "Remplacés par `self.project_title` et `self.info_line`. "
        "Si du code externe accède à ces attributs, il va crasher.\n"
        "  - ⚠️ **BREAKING** : `self.rebuild_button` supprimé + méthode `_open_packaging_guide()` supprimée.\n\n"
        "**3. `app/services/project_pilotage.py`**\n"
        "- `_build_project_html()` :\n"
        "  - Ajout d'un bloc `report_card` (Now/Next/Blockers) en haut du HTML, avant les grid4 metrics\n"
        "  - Section `On est où?` : remplacé les `<ul><li>Repos: N</li>…` par des `<span class='badge'>` horizontaux avec emojis HTML entities\n"
        "  - `On s en va ou?` → `On s'en va où?` (accents corrigés)\n"
        "  - Ajout variable `now_items = state.get('now', [])` pour alimenter le Now du report_card\n"
        "  - **Impact** : la structure HTML a changé. Si des tests comparent le HTML exact, ils vont casser.\n\n"
        "**4. `app/ui/theme.qss`**\n"
        "- Ajout 4 règles `QFrame#agentCard[status-stripe=…]` pour les bordures gauches\n"
        "- Ajout `QLabel#runtimeContextTitle` (bold 13px)\n"
        "- Ajout `QLabel#agentTaskHeader` (9px bold gris)\n"
        "- Status pills : padding `3px 10px` (was `2px 8px`), `font-weight: 700` (was `600`), couleurs légèrement ajustées\n\n"
        "---\n\n"
        "## Session 2 : Fix des 3 bugs de Clems\n\n"
        "**Bug 1 (P0) — `control/projects/cockpit/agents/leo/state.json`**\n"
        "- `blockers: []` (was `[\"Operational blocker: stale ping…\"]`)\n"
        "- `current_task: \"\"` (was `\"Wave 1 UI delegation active with @agent-6,@agent-7\"`)\n"
        "- `percent: 0` (was `100`)\n\n"
        "**Bug 3 (P1) — `app/ui/agents_grid.py`**\n"
        "- `AgentCard.__init__()` : ajout override → si `state.blockers` non-vide ET `status_key == 'rest'`, force `status_key = 'blocked'` et `status_text = '🔴 Bloqué (blockers)'`\n"
        "- Ajout rendu blockers : QLabel `agentBlockersHeader` (⚠️ BLOCKERS) + jusqu'à 3 QLabel `agentBlocker` (• texte)\n"
        "- `theme.qss` : ajout styles `agentBlockersHeader` (rouge 991B1B, 9px bold) + `agentBlocker` (rouge C94B4B, 11px)\n\n"
        "---\n\n"
        "## Points de conflit potentiels\n\n"
        "1. **`sidebar.py` RuntimeContextPanel** — si ta branche a du code qui accède à `self.app_stamp`, `self.repo_head`, `self.project_context`, ou `self.rebuild_button`, ça va crasher.\n"
        "2. **`project_pilotage.py` HTML structure** — le HTML généré a changé significativement (ajout report_card, badges au lieu de listes).\n"
        "3. **`theme.qss`** — j'ai ajouté ~30 lignes de nouvelles règles QSS. Possible conflit de merge si tu as aussi touché ce fichier.\n"
        "4. **`agents_grid.py`** — l'init de `AgentCard` a changé : nouveau order des widgets dans le layout, nouvelles properties.\n\n"
        "**Questions pour toi :**\n"
        "- Est-ce que ta branche touche `sidebar.py` ou `project_pilotage.py` ?\n"
        "- Le `PermissionError` sur `clems/state.json` — c'est un lock macOS ou une protection intentionnelle ?\n\n"
        "Ping moi si tu veux un diff complet.\n"
    )

    print("Posting debug report to Clems...")
    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "high",
        "tags": ["debug", "report", "stream-ui-p0", "clems"],
    })
    print("✅ Report posted to cockpit chat.")


if __name__ == "__main__":
    asyncio.run(main())
