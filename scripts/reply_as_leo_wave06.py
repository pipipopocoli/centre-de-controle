import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

try:
    from control.mcp_server import handle_post_message
except ImportError:
    # Fallback if mcp_server is not directly importable or in a different path structure
    sys.path.append(str(PROJECT_ROOT / "control"))
    from mcp_server import handle_post_message

async def main():
    agent_id = "leo"
    project_id = "cockpit"

    msg = (
        "@clems @nova @victor\n"
        "**Wave 06 Ack (UI Lane)**\n"
        "Now: Vue sur l'activation Wave 06 (Nova L1 + Timeline Lock backend passés).\n"
        "Je maintiens la veille sur l'évidence UI du feed timeline pour garantir que le tri déterministe est bien reflété visuellement.\n"
        "Next: Validation visuelle (screenshot proof) si drifts détectés on render.\n"
        "Blockers: none."
    )

    print("Posting Leo's Wave 06 Ack to Clems/Team...")
    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "normal",
        "tags": ["wave06", "ui", "ack", "clems"],
    })
    print("✅ Report posted to cockpit chat.")


if __name__ == "__main__":
    asyncio.run(main())
