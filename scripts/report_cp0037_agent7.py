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
    agent_id = "agent-7"
    project_id = "cockpit"

    msg = (
        "@leo @clems\n"
        "**Wave 09 Ack (CP-0037 Evidence Pack Mapping)**\n"
        "Now: Created and mapped all screenshot artifacts for normal and degraded states in `CP0037_QA_EVIDENCE_PACK_2026-02-21.md`. Proof links for CP37-01 through CP37-05 are mapped to their respective Simple/Tech modes.\n"
        "Next: CP-0037 lane is fully closed out with operator-grade visibility evidence locked. Ready for next mission or CAD wave synchronization.\n"
        "Blockers: None."
    )

    print(f"Posting Agent 7's Wave 09 Ack to {project_id} chat...")
    try:
        await handle_post_message({
            "agent_id": agent_id,
            "project_id": project_id,
            "content": msg,
            "priority": "normal",
            "tags": ["wave09", "cp0037", "qa", "status", "evidence"],
        })
        print("✅ Report posted successfully.")
    except Exception as e:
        print(f"❌ Failed to post report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
