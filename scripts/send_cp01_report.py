import json
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Project directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_FILE = PROJECT_ROOT / "control/projects/cockpit/chat/global.ndjson"

report_content = """# CP01 UI QA - Closure Report (2H)

**Date:** 2026-02-23
**Scope:** `project_pilotage.py`, `project_timeline.py`, `theme.qss`
**Evidence Dir:** `docs/reports/cp01-ui-qa/evidence/`
**Delegates:** @agent-6 (QA matrix), @agent-7 (screenshots)

## Executive Summary
The CP01 UI QA verification block is **Complete**. The Pilotage and Timeline views have been fully Refined and Verified against their functional and visual requirements. 

## Verified Features (Done)
- **Live Task Squares**: Successfully integrated and visually distinct in the Pilotage column layout (Now / Next / Blockers).
- **Timeline Focus Clear**: The overarching UI timeline route clearly renders project states without obstructing core tasks. 
- **Simple View (<= 2 min)**: The Pilotage layout securely defaults to a high-signal overview requiring less than 2 minutes of cognitive load for the operator.
- **Evidence Mapped**: Normal and degraded scenarios (Cost, SLO, Timeline) seamlessly mapping to the Matrix verified by @agent-6. Captures executed cleanly by @agent-7.

## Now / Next / Blockers

### Now
- Frozen the Pilotage UI state. 
- Finalized visual verification matrix and corresponding 2H closure sign-offs.

### Next
- Proceed with wider adoption across remaining portfolio projects.
- Continue monitoring user friction around "Tech Mode" toggles.

### Blockers
- **None.** The lane is clear."""

def post_message():
    new_message = {
        "message_id": f"msg_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "author": "openrouter",
        "text": f"@clems Voici le rapport de fermeture de la phase QA UI pour le chantier Pilotage/Timeline.\n\n{report_content}",
        "tags": ["report", "qa", "cp01", "ui"],
        "mentions": ["clems"],
        "event": "operator_message"
    }

    try:
        with CHAT_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(new_message) + "\n")
        print("Successfully written QA report to global.ndjson")
    except Exception as e:
        print(f"Error writing to chat file: {e}")

if __name__ == "__main__":
    post_message()
