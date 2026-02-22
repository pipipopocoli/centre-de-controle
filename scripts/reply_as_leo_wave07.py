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
        "@clems @victor\n"
        "**Wave 07 Ack (UI Polish)**\n"
        "Now: Wave07 UI Polish implemented. Simple vs Tech modes are distinct. Degraded states use clear Amber/Red signals.\n"
        "Next: Visual sign-off pending local verification (QA env issues).\n"
        "Blockers: none."
    )

    print(f"Posting Leo's Wave 07 Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave07", "ui", "ack", "status"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
