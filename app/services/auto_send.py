from __future__ import annotations

import subprocess
from dataclasses import dataclass

from app.services.auto_mode import AutoModeAction


@dataclass(frozen=True)
class SendRoute:
    project_id: str
    agent_id: str
    platform: str
    app_name: str
    window_title_contains: str
    require_window_match: bool


@dataclass(frozen=True)
class SendResult:
    sent: bool
    status: str
    app_name: str
    agent_id: str
    window_title: str
    error: str


def _run_osascript(script: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, (completed.stdout or "").strip(), (completed.stderr or "").strip()


def _activate_app(app_name: str) -> tuple[bool, str]:
    completed = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout or "open failed").strip()
    code, _out, err = _run_osascript(f'tell application "{app_name}" to activate')
    if code != 0:
        return False, err or "activate failed"
    return True, ""


def _front_window_title(app_name: str) -> tuple[bool, str, str]:
    script = (
        'tell application "System Events"\n'
        f'  if not (exists process "{app_name}") then return "__NO_PROCESS__"\n'
        f'  tell process "{app_name}"\n'
        "    if (count of windows) is 0 then return \"__NO_WINDOW__\"\n"
        "    return name of front window\n"
        "  end tell\n"
        "end tell"
    )
    code, out, err = _run_osascript(script)
    if code != 0:
        return False, "", err or "window title read failed"
    return True, out, ""


def _send_clipboard_enter(app_name: str, prompt_text: str) -> tuple[bool, str]:
    copy = subprocess.run(["pbcopy"], input=prompt_text, text=True, capture_output=True, check=False)
    if copy.returncode != 0:
        return False, (copy.stderr or copy.stdout or "pbcopy failed").strip()
    script = (
        f'tell application "{app_name}" to activate\n'
        "delay 0.15\n"
        'tell application "System Events"\n'
        '  keystroke "v" using command down\n'
        "  delay 0.05\n"
        "  key code 36\n"
        "end tell"
    )
    code, _out, err = _run_osascript(script)
    if code != 0:
        return False, err or "send keystrokes failed"
    return True, ""


def send_action(action: AutoModeAction, route: SendRoute, dry_run: bool = False) -> SendResult:
    lock_marker = f"PROJECT LOCK: {route.project_id}"
    if lock_marker not in action.prompt_text:
        return SendResult(
            sent=False,
            status="missing_project_lock",
            app_name=route.app_name,
            agent_id=route.agent_id,
            window_title="",
            error=f"missing prompt marker: {lock_marker}",
        )

    ok, activate_error = _activate_app(route.app_name)
    if not ok:
        return SendResult(
            sent=False,
            status="error",
            app_name=route.app_name,
            agent_id=route.agent_id,
            window_title="",
            error=activate_error,
        )

    ok, window_title, window_error = _front_window_title(route.app_name)
    if not ok:
        lowered = window_error.lower()
        status = "permission_denied" if "not authorized" in lowered or "not allowed" in lowered else "error"
        return SendResult(
            sent=False,
            status=status,
            app_name=route.app_name,
            agent_id=route.agent_id,
            window_title="",
            error=window_error,
        )

    expected = (route.window_title_contains or "").strip().lower()
    if route.require_window_match and expected:
        current = (window_title or "").strip().lower()
        if expected not in current:
            return SendResult(
                sent=False,
                status="window_mismatch",
                app_name=route.app_name,
                agent_id=route.agent_id,
                window_title=window_title,
                error=f'window title mismatch: expected "{route.window_title_contains}", got "{window_title}"',
            )

    if dry_run:
        return SendResult(
            sent=False,
            status="dry_run",
            app_name=route.app_name,
            agent_id=route.agent_id,
            window_title=window_title,
            error="",
        )

    ok, send_error = _send_clipboard_enter(route.app_name, action.prompt_text)
    if not ok:
        lowered = send_error.lower()
        status = "permission_denied" if "not authorized" in lowered or "not allowed" in lowered else "error"
        return SendResult(
            sent=False,
            status=status,
            app_name=route.app_name,
            agent_id=route.agent_id,
            window_title=window_title,
            error=send_error,
        )

    return SendResult(
        sent=True,
        status="sent",
        app_name=route.app_name,
        agent_id=route.agent_id,
        window_title=window_title,
        error="",
    )

