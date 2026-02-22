import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

try:
    from control.mcp_server import handle_post_message
except ImportError:
    # Fallback if mcp_server is not directly importable or in a different path structure
    # This mimics the structure seen in other scripts
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message

async def main():
    agent_id = "antigravity"
    project_id = "cockpit"

    msg = (
        "**@clems — Rapport Wave 06 : Nova Global L1 + Timeline Lock**\n\n"
        "La Wave 06 est initiée et les objectifs backend sont atteints.\n\n"
        "---\n\n"
        "## ✅ Accomplissements\n\n"
        "**1. Nova Global L1 (Creative Science Lead)**\n"
        "- `MISSION-AGENT6-WAVE06.md` et `ISSUE-CP-0033` créés.\n"
        "- Fallback explicite vers Nova (via `antigravity`) implémenté dans `agent_registry.py` et `auto_mode.py`.\n"
        "- Vérification : `tests/verify_wave06_nova.py` **PASS**.\n\n"
        "**2. Timeline Feed Lock**\n"
        "- Tri déterministe verrouillé dans `timeline_feed.py` (Clé primaire: Event ID + Source + Title).\n"
        "- Vérification : `tests/verify_timeline_deterministic.py` **PASS**.\n\n"
        "**3. Evidence QA**\n"
        "- Pack de preuves pour `CP01 Hybrid Timeline` (Normal + Degraded) généré et validé.\n\n"
        "---\n\n"
        "## ⏭️ Next Steps\n\n"
        "- Monitoring du comportement de Nova en tant que L1 global.\n"
        "- Passation pour validation finale.\n\n"
        "Le système est prêt pour la suite.\n"
    )

    print("Posting Wave 06 report to Clems...")
    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "high",
        "tags": ["report", "wave06", "nova", "clems"],
    })
    print("✅ Report posted to cockpit chat.")


if __name__ == "__main__":
    asyncio.run(main())
