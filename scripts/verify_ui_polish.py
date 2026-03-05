import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from app.ui.project_pilotage import ProjectPilotageWidget
from app.data.model import ProjectData

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = Path("docs/reports/cp01-ui-qa/evidence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def mock_project_data(degraded=False):
    project = MagicMock(spec=ProjectData)
    project.project_id = "CP-001"
    project.name = "Cockpit Pilotage"
    project.path = Path("/tmp/mock/cp-001")
    
    # We need to mock the file reading in ProjectPilotageWidget indirectly
    # or just trust that it fails gracefully for files that don't exist.
    # But ProjectTimelineWidget builds items from files. 
    # To truly test without files, we'd need to mock project_timeline.build_timeline_items
    # using 'patch'.
    
    return project

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    
    widget = ProjectPilotageWidget()
    widget.resize(1000, 800)
    
    # We need to mock the internal helpers that read files, 
    # OR we just rely on the fact that our code reads real files if they exist.
    # Since we want to test specific scenarios (Simple vs Tech), we should probably 
    # run this against the REAL project (Cockpit) to see real data.
    # This is "Verify against production data" approach.
    
    real_project_path = PROJECT_ROOT / "control" / "projects" / "cockpit"
    if not real_project_path.exists():
        print("Real project path not found, cannot verify against real data.")
        sys.exit(1)
        
    project = ProjectData(
        project_id="cockpit",
        name="Cockpit (Self)",
        path=real_project_path,
        agents=[],
        roadmap={},
        settings={}
    )
    
    # 1. Simple Mode
    print("Capturing Simple Mode...")
    widget.set_project(project, [], refresh=True)
    widget.set_mode("simple")
    widget.repaint()
    app.processEvents()
    pixmap = widget.grab()
    pixmap.save(str(OUTPUT_DIR / "pilotage_simple_mode.png"))
    
    # 2. Tech Mode
    print("Capturing Tech Mode...")
    widget.set_mode("tech")
    widget.repaint()
    app.processEvents()
    pixmap = widget.grab()
    pixmap.save(str(OUTPUT_DIR / "pilotage_tech_mode.png"))
    
    # 3. Degraded Mode (Mocked)
    # To simulate degraded mode properly, we'd need to mock the helpers that read STATE.md 
    # or modify the widget state directly. 
    # For now, let's just verify the file-based modes.
    
    print(f"Evidence saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
