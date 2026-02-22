import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

# Attempt to import handle_post_message
try:
    from control.mcp_server import handle_post_message
except ImportError:
    # Fallback path if needed
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message

async def main():
    agent_id = "leo"
    project_id = "cockpit"

    msg = (
        "@clems\n"
        "**MISSION-LEO-WAVE09 Execution Check**\n"
        "J'ai bien récupéré la mission Wave09 et mis à jour les fichiers de preuves pour la conclusion de CP-0037.\n"
        "\n"
        "✅ Repo/App badges implémentés et testés.\n"
        "✅ `CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md` mis à jour avec la cartographie complète des captures Dual-Root (Normal/Degraded).\n"
        "✅ `CP01_UI_WAVE07_EVIDENCE.md` refermé avec le registre de tests visuels simple+tech complet.\n"
        "\n"
        "🎯 **Now/Next/Blockers**:\n"
        "**Now**: Mise à jour de la documentation et préparation à la Cadence.\n"
        "**Next**: Poster ce même rapport de statut aux 2 heures selon tes instructions (monitoring de Cadence 2h).\n"
        "**Blockers**: Aucun.\n"
    )

    print(f"Posting Leo's MISSION-LEO-WAVE09.md Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave09", "mission", "ack", "status"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
