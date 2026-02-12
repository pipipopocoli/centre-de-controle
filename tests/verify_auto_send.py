from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import AutoModeAction
from app.services.auto_send import SendRoute, send_action


def main() -> int:
    action = AutoModeAction(
        request_id="runreq_test",
        agent_id="victor",
        prompt_text="[Cockpit auto-mode]\nPROJECT LOCK: cockpit\nDo not execute for another project.\nTask:\nping\n",
        app_to_open="Codex",
        notify_text="test",
    )
    route = SendRoute(
        project_id="cockpit",
        agent_id="victor",
        platform="codex",
        app_name="Codex",
        window_title_contains="cockpit-victor",
        require_window_match=True,
    )

    with patch("app.services.auto_send._activate_app", return_value=(True, "")), patch(
        "app.services.auto_send._front_window_title",
        return_value=(True, "cockpit-victor thread", ""),
    ), patch("app.services.auto_send._send_clipboard_enter", return_value=(True, "")):
        sent = send_action(action, route, dry_run=False)
        assert sent.status == "sent" and sent.sent, "send should succeed when route matches"

    with patch("app.services.auto_send._activate_app", return_value=(True, "")), patch(
        "app.services.auto_send._front_window_title",
        return_value=(True, "other-project-thread", ""),
    ):
        mismatch = send_action(action, route, dry_run=True)
        assert mismatch.status == "window_mismatch", "window mismatch must block send"

    wrong_lock_action = AutoModeAction(
        request_id="runreq_wrong_lock",
        agent_id="victor",
        prompt_text="[Cockpit auto-mode]\nPROJECT LOCK: demo\nTask:\nping\n",
        app_to_open="Codex",
        notify_text="test",
    )
    lock_fail = send_action(wrong_lock_action, route, dry_run=True)
    assert lock_fail.status == "missing_project_lock", "missing lock marker must be blocked"

    with patch("app.services.auto_send._activate_app", return_value=(True, "")), patch(
        "app.services.auto_send._front_window_title",
        return_value=(False, "", "Not authorized to send Apple events to System Events."),
    ):
        denied = send_action(action, route, dry_run=True)
        assert denied.status == "permission_denied", "permission errors should be explicit"

    print("OK: auto-send verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
