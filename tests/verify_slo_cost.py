
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.data.model import ProjectData, AgentState
from app.services.project_pilotage import _slo_verdict_card, _cost_panel_card

def test_slo_scenarios():
    print("\n=== Testing SLO Scenarios ===")
    
    # Mock Project
    project = MagicMock(spec=ProjectData)
    project.settings = {
        "slo": {
            "targets": {
                "dispatch_p95_ms": 5000,
                "dispatch_p99_ms": 12000,
                "success_rate_min": 0.95
            }
        }
    }

    # Scenario SLO-001: GO
    # Blockers = 0, Pending <= 3
    print("Running SLO-001: GO ...", end=" ")
    html = _slo_verdict_card(project, pending=3, blockers_open=0)
    assert "GO" in html
    assert "#166534" in html  # Green color
    print("PASS")

    # Scenario SLO-002: HOLD (Blocker)
    # Blockers > 0
    print("Running SLO-002: HOLD (Blocker) ...", end=" ")
    html = _slo_verdict_card(project, pending=0, blockers_open=1)
    assert "HOLD" in html
    assert "#92400E" in html or "#C94B4B" in html # Check for HOLD color or red text
    print("PASS")

    # Scenario SLO-003: HOLD (Queue)
    # Pending > 3
    print("Running SLO-003: HOLD (Queue) ...", end=" ")
    html = _slo_verdict_card(project, pending=4, blockers_open=0)
    assert "HOLD" in html
    print("PASS")

    # Scenario SLO-004: HOLD (Both)
    print("Running SLO-004: HOLD (Both) ...", end=" ")
    html = _slo_verdict_card(project, pending=4, blockers_open=1)
    assert "HOLD" in html
    print("PASS")
    
    # Scenario SLO-005: Missing Config
    print("Running SLO-005: Missing Config ...", end=" ")
    empty_project = MagicMock(spec=ProjectData)
    empty_project.settings = {}
    html = _slo_verdict_card(empty_project, pending=0, blockers_open=0)
    assert "GO" in html # Default should be GO
    print("PASS")

def test_cost_scenarios():
    print("\n=== Testing Cost Scenarios ===")

    # Scenario COST-001: No Budget
    print("Running COST-001: No Budget ...", end=" ")
    project_no_budget = MagicMock(spec=ProjectData)
    project_no_budget.settings = {"cost": {"monthly_budget_cad": 0}}
    html = _cost_panel_card(project_no_budget)
    assert "Aucun budget configur" in html
    assert "n/a" in html
    print("PASS")

    # Scenario COST-002: Budget Displayed
    print("Running COST-002: Budget Displayed ...", end=" ")
    project_budget = MagicMock(spec=ProjectData)
    project_budget.settings = {"cost": {"monthly_budget_cad": 1200, "currency": "CAD"}}
    html = _cost_panel_card(project_budget)
    assert "$1,200" in html
    assert "Co&#xFB;t mensuel" in html
    print("PASS")

if __name__ == "__main__":
    try:
        test_slo_scenarios()
        test_cost_scenarios()
        print("\nAll automated verification checks PASSED.")
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
