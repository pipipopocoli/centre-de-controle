from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, list_projects  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


STYLE = """
#sidebar {
    background: #f5f6f8;
    border-right: 1px solid #d8dadd;
}
#sidebarTitle {
    font-weight: 600;
}
#roadmap {
    background: #fdfdfd;
    border: 1px solid #d8dadd;
    border-radius: 6px;
}
#agentsGrid {
    background: #ffffff;
    border-top: 1px solid #d8dadd;
}
#agentCard {
    background: #f8f9fb;
    border: 1px solid #e0e2e5;
    border-radius: 6px;
}
#agentCard[stale="true"] {
    background: #fff5f5;
    border: 1px solid #d69b9b;
}
#agentBadge {
    background: #1b6ef3;
    color: #ffffff;
    border-radius: 4px;
    padding: 2px 4px;
    font-size: 10px;
}
#chatroom {
    background: #f9fafc;
    border-left: 1px solid #d8dadd;
}
#chatroomTitle {
    font-weight: 600;
}
#agentHeartbeat[stale="true"] {
    color: #b03030;
    font-weight: 600;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    project = ensure_demo_project()
    projects = list_projects()

    window = MainWindow(project, projects=projects)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
