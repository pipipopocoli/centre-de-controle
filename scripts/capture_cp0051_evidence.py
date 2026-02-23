import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from app.ui.project_pilotage import ProjectPilotageWidget
from app.data.model import ProjectData

OUTPUT_DIR = Path("docs/reports/cp01-ui-qa/evidence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def mock_subprocess_run_normal(*args, **kwargs):
    res = MagicMock()
    res.returncode = 0
    payload = {
        "status": "healthy",
        "issues": []
    }
    res.stdout = f"{json.dumps(payload)}\n"
    return res

def mock_subprocess_run_degraded(*args, **kwargs):
    res = MagicMock()
    res.returncode = 0
    payload = {
        "status": "degraded",
        "issues": ["snapshot_stale", "latency_high"]
    }
    res.stdout = f"{json.dumps(payload)}\n"
    return res

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    
    widget = ProjectPilotageWidget()
    widget.resize(1100, 900)
    
    real_project_path = Path("/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit")
    
    project = ProjectData(
        project_id="cockpit",
        name="Cockpit (Self)",
        path=real_project_path,
        agents=[],
        roadmap={},
        settings={}
    )
    
    # 1. Capture Normal State (Simple + Tech)
    print("Capturing Normal / Simple Mode...")
    with patch('subprocess.run', side_effect=mock_subprocess_run_normal):
        widget.set_project(project, [], refresh=True)
        widget.set_mode("simple")
        widget.repaint()
        app.processEvents()
        pixmap = widget.grab()
        pixmap.save(str(OUTPUT_DIR / "cp0051_normal_simple.png"))

    print("Capturing Normal / Tech Mode...")
    with patch('subprocess.run', side_effect=mock_subprocess_run_normal):
        widget.set_mode("tech")
        widget.repaint()
        app.processEvents()
        pixmap = widget.grab()
        pixmap.save(str(OUTPUT_DIR / "cp0051_normal_tech.png"))

    # 2. Capture Degraded State (Simple + Tech)
    print("Capturing Degraded / Simple Mode...")
    with patch('subprocess.run', side_effect=mock_subprocess_run_degraded):
        widget.set_project(project, [], refresh=True)
        widget.set_mode("simple")
        widget.repaint()
        app.processEvents()
        pixmap = widget.grab()
        pixmap.save(str(OUTPUT_DIR / "cp0051_degraded_simple.png"))

    print("Capturing Degraded / Tech Mode...")
    with patch('subprocess.run', side_effect=mock_subprocess_run_degraded):
        widget.set_mode("tech")
        widget.repaint()
        app.processEvents()
        pixmap = widget.grab()
        pixmap.save(str(OUTPUT_DIR / "cp0051_degraded_tech.png"))

    print("All CP-0051 captures complete.")

if __name__ == "__main__":
    main()
