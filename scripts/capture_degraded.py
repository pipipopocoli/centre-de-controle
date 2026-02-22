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

def mock_subprocess_run(*args, **kwargs):
    res = MagicMock()
    res.returncode = 0
    # Provide a degraded status payload
    payload = {
        "status": "degraded",
        "issues": ["snapshot_stale", "latency_high"]
    }
    res.stdout = f"{json.dumps(payload)}\n"
    return res

@patch('subprocess.run', side_effect=mock_subprocess_run)
def main(mock_run):
    app = QApplication.instance() or QApplication(sys.argv)
    
    widget = ProjectPilotageWidget()
    widget.resize(1000, 800)
    
    real_project_path = Path("/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit")
    
    project = ProjectData(
        project_id="cockpit",
        name="Cockpit (Self)",
        path=real_project_path,
        agents=[],
        roadmap={},
        settings={}
    )
    
    # Tech Mode Degraded
    print("Capturing Tech Mode Degraded...")
    widget.set_project(project, [], refresh=True)
    widget.set_mode("tech")
    widget.repaint()
    app.processEvents()
    
    pixmap = widget.grab()
    out_path = OUTPUT_DIR / "pilotage_tech_mode_degraded.png"
    pixmap.save(str(out_path))
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
