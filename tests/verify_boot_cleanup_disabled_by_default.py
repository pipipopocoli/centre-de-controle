#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import BOOT_CLEANUP_ENV, _maybe_boot_cleanup  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_dir = projects_root / "cockpit"
        (project_dir / "runs").mkdir(parents=True, exist_ok=True)
        (project_dir / "chat").mkdir(parents=True, exist_ok=True)
        marker = project_dir / "runs" / "marker.txt"
        marker.write_text("keep", encoding="utf-8")

        os.environ.pop(BOOT_CLEANUP_ENV, None)
        removed = _maybe_boot_cleanup(projects_root)

        assert removed == []
        assert marker.exists(), "boot cleanup must stay disabled by default"
        assert (project_dir / "chat").exists(), "chat directory must remain untouched"

    print("OK: boot cleanup disabled by default verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
