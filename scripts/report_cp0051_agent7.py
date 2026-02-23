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
    agent_id = "agent-7"
    project_id = "cockpit"

    msg = (
        "@leo @clems\n"
        "**Wave 14 UI Readability (CP-0051 Evidence Pack)**\n"
        "Now: Created and mapped all screenshot artifacts for normal and degraded states in `WAVE14_UI_EVIDENCE_MAPPING.md`. Captures include hierarchy, timeline, and live squares.\n"
        "Next: Ready for next task.\n"
        "Blockers: None."
    )

    print(f"Posting Agent 7's Wave 14 Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave14", "cp0051", "qa", "status", "evidence"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
