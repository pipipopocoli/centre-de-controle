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
    project_id = "cockpit"

    print("Updating Agent Status...")
    await handle_update_agent_state({
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "completed",
        "current_task": "SLO/Cost QA Scenario Matrix",
        "current_phase": "Review",
        "blockers": [],
        "metadata": {
             "now": "QA Completed — 7/7 PASS",
             "next": "Await review / next assignment",
             "blockers": "None"
        }
    })

    print("Posting Report...")
    msg = (
        "**SLO/Cost QA Scenario Matrix — COMPLETE**\n\n"
        "**Coverage**: 100% (7/7 scenarios)\n\n"
        "**SLO Verdict Logic (5 scenarios)**:\n"
        "- ✅ SLO-001: GO (clean state) — PASS\n"
        "- ✅ SLO-002: HOLD (blocker present) — PASS\n"
        "- ✅ SLO-003: HOLD (queue overflow >3) — PASS\n"
        "- ✅ SLO-004: HOLD (both failures) — PASS\n"
        "- ✅ SLO-005: Missing config → defaults — PASS\n\n"
        "**Cost Panel Logic (2 scenarios)**:\n"
        "- ✅ COST-001: No budget → 'n/a' — PASS\n"
        "- ✅ COST-002: Budget $1,200/mois — PASS\n\n"
        "**Artifacts**:\n"
        "- `tests/verify_slo_cost.py` — automated repro script\n"
        "- `QA_SCENARIO_MATRIX.md` — full matrix with repro steps\n\n"
        "**Now**: QA Complete. All scenarios verified.\n"
        "**Next**: Awaiting review or next assignment.\n"
        "**Blockers**: None."
    )

    await handle_post_message({
        "agent_id": agent_id,
        "project_id": project_id,
        "content": msg,
        "priority": "normal",
        "tags": ["slo", "cost", "qa", "report"]
    })

    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
