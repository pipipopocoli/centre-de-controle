from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def run_codex(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    output_path: Path | None = None,
) -> RunnerResult:
    started_at = _utc_now_iso()
    started_mono = time.monotonic()

    managed_output = output_path is None
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(prefix="cockpit_codex_", suffix=".txt", delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "codex",
        "exec",
        "--full-auto",
        "--skip-git-repo-check",
        "--cd",
        str(cwd),
        "--output-last-message",
        str(output_path),
        prompt,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(int(timeout_s), 30),
        )
        duration = max(time.monotonic() - started_mono, 0.0)
        success = completed.returncode == 0
        status = "completed" if success else "failed"
        error = None if success else (completed.stderr.strip() or completed.stdout.strip() or "codex exec failed")
        output_text = _read_text(output_path)
        return RunnerResult(
            runner="codex",
            status=status,
            success=success,
            launched=True,
            completed=True,
            returncode=completed.returncode,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
            error=error,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text=output_text,
        )
    except subprocess.TimeoutExpired as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="codex",
            status="timeout",
            success=False,
            launched=True,
            completed=False,
            returncode=None,
            stdout=(exc.stdout or "").strip(),
            stderr=(exc.stderr or "").strip(),
            error=f"codex exec timeout after {max(int(timeout_s), 30)}s",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    except OSError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="codex",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"codex exec unavailable: {exc}",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    finally:
        if managed_output and output_path is not None:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass
