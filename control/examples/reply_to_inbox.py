import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

# Ensure control module can be imported
try:
    from control.mcp_server import handle_post_message, handle_update_agent_state
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message, handle_update_agent_state

CHAT_FILE = PROJECT_ROOT / "control/projects/demo/chat/global.ndjson"

async def main():
    agent_id = "antigravity"
    project_id = "cockpit-5"
    
    
    # 2. Update Agent State (Active)
    await handle_update_agent_state({
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "executing",
        "current_task": "Replying to Brain Manager update",
        "current_phase": "Review"
    })

    # 3. Post Reply (Simulating Operator Answers)
    reply_content = (
        "Project Intake Answers:\n\n"
        "1. Cockpit est un dashboard local pour superviser des agents IOA. Utilisateur: Développeur/Solo-preneur.\n"
        "2. `pytest` pour les tests unitaires.\n"
        "3. Local uniquement (Mac).\n"
        "4. Aucune variable d'env obligatoire pour le moment (tout est local).\n"
        "5. Objectifs: 1. UI Clarity (V6), 2. Deep Mining integration, 3. BrainFS profiles.\n"
        "6. Risques: Complexité UI et permissions macOS.\n"
    )
    
    msg_args = {
        "agent_id": "operator", # Simulate operator
        "content": reply_content,
        "project_id": project_id,
        "priority": "high",
        "tags": ["answers", "intake"],
        "metadata": {}
    }
    
    try:
        result = await handle_post_message(msg_args)
        print(f"Reply posted: {result[0].text if result else 'No result'}")
    except Exception as e:
        print(f"Error posting reply: {e}")

    # 4. Update Agent State (Idle)
    await handle_update_agent_state({
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "idle",
        "current_task": "Monitoring",
        "current_phase": "Review"
    })

if __name__ == "__main__":
    asyncio.run(main())
