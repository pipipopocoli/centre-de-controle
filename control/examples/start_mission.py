import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

# Ensure control module can be imported
try:
    from control.mcp_server import handle_post_message, handle_update_agent_state
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message, handle_update_agent_state

async def main():
    agent_id = "antigravity"
    project_id = "demo"
    
    print("Updating Agent Status...")
    await handle_update_agent_state({
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "executing",
        "current_task": "Verifying Brain Hardening",
        "current_phase": "Test",
        "blockers": [],
        "metadata": {
             "now": "Executer verify_brain_hardening.py",
             "next": "Rapport et analyse",
             "blockers": "None"
        }
    })

    print("Posting Mission Acknowledgment...")
    msg = (
        "Mission reçue. Début de l'exécution.\n\n"
        "**Now**: Exécution des tests de hardening (`tests/verify_brain_hardening.py`)\n"
        "**Next**: Analyse des résultats et rapport\n"
        "**Blockers**: Aucun"
    )
    
    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "normal", 
        "tags": ["status", "mission", "executing"]
    })

if __name__ == "__main__":
    asyncio.run(main())
