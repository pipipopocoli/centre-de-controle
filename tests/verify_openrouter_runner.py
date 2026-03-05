from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.openrouter_runner import run_openrouter, run_openrouter_exec  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        output_path = cwd / "openrouter_out.txt"

        with patch(
            "app.services.openrouter_runner._chat_completion",
            return_value=("runner output", '{"id":"ok"}'),
        ):
            result = run_openrouter("PROJECT LOCK: cockpit", cwd=cwd, timeout_s=60, output_path=output_path)
            assert result.success is True
            assert result.status == "completed"
            assert result.completed is True
            assert result.output_text == "runner output"

        with patch("app.services.openrouter_runner._chat_completion", side_effect=RuntimeError("boom")):
            result = run_openrouter("PROJECT LOCK: cockpit", cwd=cwd, timeout_s=60, output_path=output_path)
            assert result.success is False
            assert result.status == "failed"
            assert "boom" in (result.error or "")

        schema_path = cwd / "schema.json"
        schema_path.write_text("{}", encoding="utf-8")
        exec_output = cwd / "openrouter_exec_out.json"

        with patch(
            "app.services.openrouter_runner._chat_completion",
            return_value=('{"ok":true}', '{"id":"ok"}'),
        ):
            result = run_openrouter_exec(
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
            assert result.output_text == '{"ok":true}'

    print("OK: openrouter runner verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
