from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ANTIGRAVITY_CLI = Path("/Applications/Antigravity.app/Contents/Resources/app/bin/antigravity")


@dataclass(frozen=True)
class RunnerResult:
    runner: str
    status: str
    success: bool
    launched: bool
    completed: bool
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None
    started_at: str
    finished_at: str
    duration_seconds: float
    command: list[str]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def launch_chat(
    prompt: str,
    cwd: Path,
    mode: str = "agent",
    reuse_window: bool = True,
    cli_path: Path = ANTIGRAVITY_CLI,
) -> RunnerResult:
    started_at = _utc_now_iso()
    started_mono = time.monotonic()

    command = [str(cli_path), "chat", "--mode", mode]
    if reuse_window:
        command.append("--reuse-window")
    command.append(prompt)

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        duration = max(time.monotonic() - started_mono, 0.0)
        success = completed.returncode == 0
        return RunnerResult(
            runner="antigravity",
            status="launched" if success else "failed",
            success=success,
            launched=success,
            completed=False,
            returncode=completed.returncode,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
            error=None if success else (completed.stderr.strip() or completed.stdout.strip() or "antigravity launch failed"),
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            command=command,
        )
    except OSError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="antigravity",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"antigravity CLI unavailable: {exc}",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            command=command,
        )
