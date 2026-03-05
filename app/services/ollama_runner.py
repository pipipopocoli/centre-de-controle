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
    output_path: str | None
    output_text: str
    model: str


def run_ollama(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    *,
    model: str = "llama3.2",
    output_path: Path | None = None,
) -> RunnerResult:
    _ = model
    # Legacy compatibility shim. Runtime is OpenRouter-only.
    result = run_openrouter(prompt, cwd=cwd, timeout_s=timeout_s, output_path=output_path)
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
        output_path=result.output_path,
        output_text=result.output_text,
        model="openrouter",
    )
