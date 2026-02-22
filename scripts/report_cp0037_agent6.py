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
    agent_id = "agent-6"
    project_id = "cockpit"

    msg = (
        "@leo @clems\n"
        "**Wave 09 Ack (CP-0037 Scenario Matrix)**\n"
        "Now: Finalized the CP-0037 scenario matrix (`CP0037_QA_SCENARIO_MATRIX_2026-02-21.md`) covering Simple/Tech modes, repo/app boundaries, and degraded states with pass/fail + repro + expected.\n"
        "Next: Hand over to @agent-7 for screenshot mapping and final evidence packet compilation.\n"
        "Blockers: None."
    )

    print(f"Posting Agent 6's Wave 09 Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave09", "cp0037", "qa", "status"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
