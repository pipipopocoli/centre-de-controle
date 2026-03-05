from __future__ import annotations

from pathlib import Path

from app.services.openrouter_runner import RunnerResult, run_openrouter, run_openrouter_exec


def run_codex(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    output_path: Path | None = None,
) -> RunnerResult:
    # Legacy compatibility shim. Runtime is OpenRouter-only.
    return run_openrouter(prompt, cwd=cwd, timeout_s=timeout_s, output_path=output_path)


def run_codex_exec(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    *,
    sandbox_mode: str = "read-only",
    approval_policy: str = "never",
    output_schema_path: Path | None = None,
    output_last_message_path: Path | None = None,
    ephemeral: bool = True,
) -> RunnerResult:
    # Legacy compatibility shim. Runtime is OpenRouter-only.
    return run_openrouter_exec(
        prompt,
        cwd=cwd,
        timeout_s=timeout_s,
        sandbox_mode=sandbox_mode,
        approval_policy=approval_policy,
        output_schema_path=output_schema_path,
        output_last_message_path=output_last_message_path,
        ephemeral=ephemeral,
    )
