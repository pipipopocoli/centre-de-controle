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
        "status": "completed",
        "current_task": "QA Agent Cards Visuals",
        "current_phase": "Review",
        "blockers": [],
        "metadata": {
             "now": "QA Completed",
             "next": "Await Review",
             "blockers": "None"
        }
    })

    print("Posting Report...")
    msg = (
        "**QA Visual Agent Cards terminé.**\n\n"
        "**Done**:\n"
        "- Checklist Created: `visual_qa_checklist.md`\n"
        "- Mockups Generated: Active & Blocked/Stale states.\n\n"
        "**Constats**:\n"
        "- ✅ Layout & Spacing OK.\n"
        "- ⚠️ Missing Stale Heartbeat Style (Fix prop: `QLabel#agentSignal[stale='true']`).\n"
        "- ⚠️ Risk: Long task text truncation (needs `elideMode` or `maxHeight`).\n\n"
        "**Now**: QA Completed.\n"
        "**Next**: Await review.\n"
        "**Blockers**: None."
    )
    
    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "normal", 
        "tags": ["ui-clarity", "report", "qa"]
    })

if __name__ == "__main__":
    asyncio.run(main())
