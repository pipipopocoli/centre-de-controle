from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    source_path = ROOT_DIR / "app" / "ui" / "main_window.py"
    text = source_path.read_text(encoding="utf-8")

    assert "_autokick_wizard_live(source=\"new_project\", repo_path=repo_path)" in text
    assert "_autokick_wizard_live(source=\"takeover\", repo_path=repo_path)" in text
    assert re.search(r"def\s+_autokick_wizard_live\(", text)

    print("OK: wave19 wizard live autokick wiring verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
