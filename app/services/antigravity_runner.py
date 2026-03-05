from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.openrouter_runner import run_openrouter


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


def launch_chat(
    prompt: str,
    cwd: Path,
    mode: str = "agent",
    reuse_window: bool = True,
    cli_path: Path | None = None,
) -> RunnerResult:
    _ = (mode, reuse_window, cli_path)
    # Legacy compatibility shim. Runtime is OpenRouter-only.
    result = run_openrouter(prompt, cwd=cwd, timeout_s=900)
    return RunnerResult(
        runner="openrouter",
        status=result.status,
        success=result.success,
        launched=result.launched,
        completed=result.completed,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        error=result.error,
        started_at=result.started_at,
        finished_at=result.finished_at,
        duration_seconds=result.duration_seconds,
        command=["openrouter", "exec", "--cd", str(cwd)],
    )
