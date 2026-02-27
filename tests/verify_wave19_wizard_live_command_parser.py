from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.wizard_live import parse_wizard_live_command  # noqa: E402


def main() -> int:
    command, body = parse_wizard_live_command("#wizard-live start")
    assert command == "start"
    assert body == ""

    command, body = parse_wizard_live_command("#wizard-live run focus on risks")
    assert command == "run"
    assert body == "focus on risks"

    command, body = parse_wizard_live_command("#wizard-live stop pause session")
    assert command == "stop"
    assert body == "pause session"

    command, body = parse_wizard_live_command("#wizard-live")
    assert command == "run"
    assert body == ""

    command, body = parse_wizard_live_command("wizard-live start")
    assert command is None
    assert body == ""

    command, body = parse_wizard_live_command("#wizard start")
    assert command is None
    assert body == ""

    print("OK: wave19 wizard live command parser verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
