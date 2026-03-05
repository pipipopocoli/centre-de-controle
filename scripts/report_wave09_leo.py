import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
        "**Wave 09 Ack (Pilotage Dual-Root)**\n"
        "Now: Pilotage UI exposes `repo` and `app` gate statuses using the auto_mode_healthcheck CLI output. Simple/Tech modes updated. Badges are green/red distinct.\n"
        "Next: Awaiting visual evidence capture from Agent 7 to close out CP-0037.\n"
        "Blockers: none."
    )

    print(f"Posting Leo's Wave 09 Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave09", "ui", "pilotage", "ack"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
