import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ui.sidebar import SidebarWidget
from app.data.model import ProjectData

def take_screenshots():
    app = QApplication(sys.argv)
    
    # Load stylesheet
    qss_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text())

    sidebar = SidebarWidget(projects=["cockpit", "archived_proj"], footer_text="v1.0.0")
    sidebar.resize(220, 800)
    
    # Render with Cockpit (Canonical)
    sidebar.set_runtime_context("abc1234", "def5678", "cockpit", runtime_mode="DEV LIVE")
    sidebar.show()
    app.processEvents()
    
    # Capture normal
    pixmap_normal = sidebar.grab()
    out_normal = Path(__file__).resolve().parent.parent / "docs" / "reports" / "cp01_ui_lock_normal.png"
    pixmap_normal.save(str(out_normal))
    print(f"Saved: {out_normal}")
    
    # Render with non-cockpit (Mismatch)
    sidebar.set_runtime_context("abc1234", "def5678", "archived_proj", runtime_mode="DEV LIVE")
    app.processEvents()
    
    # Capture mismatch
    pixmap_mismatch = sidebar.grab()
    out_mismatch = Path(__file__).resolve().parent.parent / "docs" / "reports" / "cp01_ui_lock_mismatch.png"
    pixmap_mismatch.save(str(out_mismatch))
    print(f"Saved: {out_mismatch}")
    
    sidebar.close()

if __name__ == "__main__":
    take_screenshots()
