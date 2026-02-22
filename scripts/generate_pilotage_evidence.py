import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.data.model import ProjectData, AgentState
from app.services import project_pilotage

# Output directory
OUTPUT_DIR = Path("docs/reports/cp01-ui-qa/evidence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_evidence():
    # Mock Project
    mock_project = ProjectData(
        project_id="CP-001",
        name="Cockpit Pilotage",
        path=Path("/tmp/mock/cp-001"),
        agents=[],
        roadmap={},
        settings={
            "slo": {
                "targets": {
                    "dispatch_p95_ms": 2000,
                    "dispatch_p99_ms": 5000,
                    "success_rate_min": 0.99
                }
            },
            "cost": {
                "currency": "CAD",
                "monthly_budget_cad": 1500
            }
        }
    )

    # Scenarios to generate
    scenarios = [
        {
            "id": "SLO-01",
            "desc": "Normal State (GO)",
            "mocks": {
                "state": {"blockers_count": 0, "phase": "Implement", "phase_pct": 45, "objective": "Ensure stability", "next_top": [], "dominant_risk": "None", "blockers": [], "gates": []},
                "issue": {"done_pct": 60, "done": 12, "total": 20},
                "agent": {"blocked": 0, "active": 2, "rest": 1, "action": 1, "waiting": 1},
                "pending": 2
            }
        },
        {
            "id": "SLO-02",
            "desc": "Degraded State (HOLD)",
            "mocks": {
                "state": {"blockers_count": 5, "phase": "Implement", "phase_pct": 45, "objective": "Fix network issues", "next_top": [], "dominant_risk": "Network Down", "blockers": ["Network Down", "API Timeout"], "gates": []},
                "issue": {"done_pct": 60, "done": 12, "total": 20},
                "agent": {"blocked": 5, "active": 0, "rest": 1, "action": 0, "waiting": 0},
                "pending": 15
            }
        },
        {
            "id": "COST-01",
            "desc": "Budget Configured",
            "mocks": {
                # Same as SLO-01 but we focus on cost
                "state": {"blockers_count": 0, "phase": "Plan", "phase_pct": 10, "objective": "Budgeting", "next_top": [], "dominant_risk": "None", "blockers": [], "gates": []},
                "issue": {"done_pct": 0, "done": 0, "total": 10},
                "agent": {"blocked": 0, "active": 0, "rest": 3, "action": 0, "waiting": 0},
                "pending": 0
            }
        },
        {
            "id": "COST-02",
            "desc": "No Budget Configured",
            "project_settings": {"cost": {"monthly_budget_cad": 0}}, # Override settings
            "mocks": {
                "state": {"blockers_count": 0, "phase": "Plan", "phase_pct": 10, "objective": "Budgeting", "next_top": [], "dominant_risk": "None", "blockers": [], "gates": []},
                "issue": {"done_pct": 0, "done": 0, "total": 10},
                "agent": {"blocked": 0, "active": 0, "rest": 3, "action": 0, "waiting": 0},
                "pending": 0
            }
        }
    ]

    with patch.object(project_pilotage, '_state_bundle') as mock_state, \
         patch.object(project_pilotage, '_issue_stats') as mock_issue, \
         patch.object(project_pilotage, '_agent_stats') as mock_agent, \
         patch.object(project_pilotage, '_pending_requests') as mock_pending, \
         patch.object(project_pilotage, '_resolve_linked_repo_path', return_value=None), \
         patch.object(project_pilotage, '_extract_first_paragraph', return_value="Mock Description"):

        for scen in scenarios:
            # Apply mocks
            m = scen["mocks"]
            mock_state.return_value = m["state"]
            mock_issue.return_value = m["issue"]
            mock_agent.return_value = m["agent"]
            mock_pending.return_value = m["pending"]

            # Adjust project settings if needed
            current_settings = mock_project.settings
            if "project_settings" in scen:
                mock_project.settings = scen["project_settings"]
            
            # Generate HTML
            html_content = project_pilotage._build_project_html(mock_project, mode="simple", portfolio=None)
            
            # Save
            filename = OUTPUT_DIR / f"scenario_{scen['id']}.html"
            filename.write_text(html_content, encoding="utf-8")
            print(f"Generated {filename}")

            # Restore settings
            mock_project.settings = current_settings

if __name__ == "__main__":
    generate_evidence()
