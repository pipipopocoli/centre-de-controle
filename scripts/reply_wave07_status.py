"""Post Victor Wave07 status + Leo ack to global chat."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit")
sys.path.append(str(PROJECT_ROOT))

# Force repo-local data path
import os
os.environ["COCKPIT_DATA_DIR"] = "repo"

from control.mcp_server import handle_post_message


async def main():
    # Victor status
    await handle_post_message({
        "agent_id": "victor",
        "project_id": "cockpit",
        "content": (
            "@clems\n"
            "**Wave 07 — Queue Dedupe Complete**\n"
            "Now: Queue cleaned (17→0 queued). Dedup guard added to store.py. "
            "4/4 tests green. Proof: docs/reports/WAVE07_QUEUE_DEDUPE_PROOF.md\n"
            "Next: Monitor for regression on next dispatch cycle.\n"
            "Blockers: none."
        ),
        "priority": "normal",
        "tags": ["wave07", "queue", "dedupe", "status"],
    })
    print("✅ Victor status posted.")

    # Leo ack — scope confirmed, no overlap with project_bible.py
    await handle_post_message({
        "agent_id": "leo",
        "project_id": "cockpit",
        "content": (
            "@clems\n"
            "**Wave 07 — Leo Scope Ack**\n"
            "Now: UI polish lane confirmed independent. No overlap with Nova's project_bible.py work.\n"
            "Next: Update evidence mapping post-backend dedupe. Continue Simple/Tech mode refinement.\n"
            "Blockers: none."
        ),
        "priority": "normal",
        "tags": ["wave07", "ui", "scope", "status"],
    })
    print("✅ Leo status posted.")


if __name__ == "__main__":
    asyncio.run(main())
