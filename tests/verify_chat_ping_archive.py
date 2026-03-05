from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.paths import project_dir  # noqa: E402
from app.data.store import (  # noqa: E402
    append_chat_message,
    append_thread_message,
    archive_ping_reminders,
    ensure_project_structure,
    load_chat_global,
    load_chat_thread,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    project_id = f"tmp-archive-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    pdir = ensure_project_structure(project_id, "Tmp Archive Test")
    try:
        ping_msg = {
            "message_id": "msg_ping_1",
            "timestamp": _utc_now_iso(),
            "author": "clems",
            "text": "Rappel @agent-1: ping en attente.",
            "tags": [],
            "mentions": ["agent-1"],
            "event": "clems_reminder",
        }
        keep_msg = {
            "message_id": "msg_keep_1",
            "timestamp": _utc_now_iso(),
            "author": "operator",
            "text": "message utile",
            "tags": [],
            "mentions": [],
        }
        append_chat_message(project_id, ping_msg)
        append_chat_message(project_id, keep_msg)
        append_thread_message(project_id, "ping", ping_msg)
        append_thread_message(project_id, "ops", keep_msg)

        summary = archive_ping_reminders(project_id, bucket="bain")
        assert int(summary.get("archived_count") or 0) == 1, summary
        archive_path = Path(str(summary.get("archive_path") or ""))
        assert archive_path.exists(), summary
        assert "chat/bain/" in str(archive_path).replace("\\", "/"), archive_path

        global_rows = load_chat_global(project_id, limit=0)
        assert all(str(row.get("event") or "") != "clems_reminder" for row in global_rows), global_rows
        assert any(str(row.get("message_id") or "") == "msg_keep_1" for row in global_rows), global_rows

        thread_rows = load_chat_thread(project_id, "ping", limit=0)
        assert not thread_rows, thread_rows
    finally:
        if pdir.exists():
            shutil.rmtree(project_dir(project_id), ignore_errors=True)

    print("OK: chat ping archive verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

