from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.codex_runner import run_codex, run_codex_exec  # noqa: E402


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

        schema_path = cwd / "schema.json"
        schema_path.write_text("{}", encoding="utf-8")
        exec_output = cwd / "codex_exec_out.json"
        exec_output.write_text("{\"ok\":true}", encoding="utf-8")

        completed = subprocess.CompletedProcess(
            args=["codex", "exec"],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("app.services.codex_runner.subprocess.run", return_value=completed) as mocked:
            result = run_codex_exec(
                "PROJECT LOCK: cockpit",
                cwd=cwd,
                timeout_s=60,
                sandbox_mode="read-only",
                approval_policy="never",
                output_schema_path=schema_path,
                output_last_message_path=exec_output,
                ephemeral=True,
            )
            assert result.success is True
            assert result.output_text == "{\"ok\":true}"
            cmd = mocked.call_args[0][0]
            assert cmd[:4] == ["codex", "-a", "never", "exec"]
            assert "-s" in cmd and "read-only" in cmd
            assert "--output-schema" in cmd
            assert "--ephemeral" in cmd

    print("OK: codex runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
