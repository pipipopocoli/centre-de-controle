from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.codex_runner import run_codex  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        output_path = cwd / "codex_out.txt"
        output_path.write_text("runner output", encoding="utf-8")

        completed = subprocess.CompletedProcess(
            args=["codex", "exec"],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("app.services.codex_runner.subprocess.run", return_value=completed):
            result = run_codex("PROJECT LOCK: cockpit", cwd=cwd, timeout_s=60, output_path=output_path)
            assert result.success is True
            assert result.status == "completed"
            assert result.completed is True
            assert result.output_text == "runner output"

        failed = subprocess.CompletedProcess(
            args=["codex", "exec"],
            returncode=1,
            stdout="",
            stderr="boom",
        )
        with patch("app.services.codex_runner.subprocess.run", return_value=failed):
            result = run_codex("PROJECT LOCK: cockpit", cwd=cwd, timeout_s=60, output_path=output_path)
            assert result.success is False
            assert result.status == "failed"
            assert "boom" in (result.error or "")

    print("OK: codex runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
