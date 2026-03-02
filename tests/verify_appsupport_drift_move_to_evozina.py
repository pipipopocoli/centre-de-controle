#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.appsupport_drift import EVOZINA_ROOT_ARTIFACTS, find_root_artifacts, move_root_artifacts  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cockpit_dir = root / "cockpit"
        evozina_dir = root / "evozina"
        cockpit_dir.mkdir(parents=True, exist_ok=True)
        evozina_dir.mkdir(parents=True, exist_ok=True)

        for filename in EVOZINA_ROOT_ARTIFACTS:
            (cockpit_dir / filename).write_text(f"{filename} from cockpit\n", encoding="utf-8")

        (evozina_dir / "INTAKE.md").write_text("existing intake\n", encoding="utf-8")

        before = find_root_artifacts(cockpit_dir)
        assert len(before) == len(EVOZINA_ROOT_ARTIFACTS)

        result = move_root_artifacts(cockpit_project_dir=cockpit_dir, evozina_project_dir=evozina_dir)
        assert len(result["moved"]) == len(EVOZINA_ROOT_ARTIFACTS)
        assert result["remaining"] == []

        after = find_root_artifacts(cockpit_dir)
        assert after == []
        assert (evozina_dir / "INTAKE.md").exists()
        assert any("INTAKE.from_cockpit_" in Path(path).name for path in result["moved"])

    print("OK: appsupport drift move to evozina verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
