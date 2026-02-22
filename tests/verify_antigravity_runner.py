from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.antigravity_runner import launch_chat  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)

        completed = subprocess.CompletedProcess(
            args=["antigravity", "chat"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch("app.services.antigravity_runner.subprocess.run", return_value=completed):
            result = launch_chat("PROJECT LOCK: cockpit", cwd=cwd, mode="agent", reuse_window=True)
            assert result.success is True
            assert result.status == "launched"
            assert result.completed is False

        failed = subprocess.CompletedProcess(
            args=["antigravity", "chat"],
            returncode=2,
            stdout="",
            stderr="fail",
        )
        with patch("app.services.antigravity_runner.subprocess.run", return_value=failed):
            result = launch_chat("PROJECT LOCK: cockpit", cwd=cwd, mode="agent", reuse_window=True)
            assert result.success is False
            assert result.status == "failed"
            assert "fail" in (result.error or "")

    print("OK: antigravity runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
