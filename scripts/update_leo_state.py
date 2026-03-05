#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "control"))

from mcp_server import handle_update_agent_state

async def main():
    agent_id = "leo"
    project_id = "cockpit"

    print(f"Updating Leo's agent state to completed for {project_id}...")
    try:
        await handle_update_agent_state({
            "agent_id": "leo",
            "project_id": "cockpit",
            "status": "completed",
            "phase": "Ship",
            "percent": 100,
            "current_task": "CP-0037 Wave09 pilotage control badges shipped.",
            "blockers": []
        })
        print("✅ Agent state updated successfully.")
    except Exception as e:
        print(f"❌ Failed to update agent state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
