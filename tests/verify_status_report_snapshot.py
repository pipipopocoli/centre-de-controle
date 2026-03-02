from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.status_report import collect_status_snapshot  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        checkout_root = root / "checkout"
        repo_root = root / "repo_project"
        appsupport_root = root / "appsupport_project"

        _write(
            checkout_root / "app" / "main.py",
            "from __future__ import annotations\n\n"
            "def main() -> int:\n"
            "    return 0\n",
        )
        _write(
            checkout_root / "docs" / "WIZARD_LIVE.md",
            "# Wizard Live\n\n- Voice: hors scope (texte only)\n",
        )
        _write(checkout_root / "scripts" / "export_status_pdf.py", "# marker\n")

        _write(
            repo_root / "STATE.md",
            "# State\n\n## Phase\n- Ship\n\n## Objective\n- Wave19 live\n\n## Now\n- run\n\n## Next\n- stabilize\n",
        )
        _write(
            appsupport_root / "STATE.md",
            "# State\n\n## Phase\n- Plan\n\n## Objective\n- Intake evozina\n\n## Now\n- intake\n\n## Next\n- roadmap\n",
        )
        _write(
            repo_root / "ROADMAP.md",
            "# Roadmap\n\n## Priorities\n- P0 wave19\n",
        )
        _write(
            appsupport_root / "ROADMAP.md",
            "# Roadmap\n\n## Next\n- setup\n",
        )
        _write(repo_root / "DECISIONS.md", "# Decisions\n\n## ADR-1\n- Accepted\n")
        _write(appsupport_root / "DECISIONS.md", "# Decisions\n\n## ADR-2\n- Accepted\n")

        provided_checks = {
            "tests": [
                {
                    "name": "tests/verify_wave19_wizard_live_command_parser.py",
                    "command": "python tests/verify_wave19_wizard_live_command_parser.py",
                    "returncode": 0,
                    "ok": True,
                    "stdout": "OK",
                    "stderr": "",
                }
            ],
            "scripts": [],
        }

        snapshot = collect_status_snapshot(
            project_id="cockpit",
            repo_root=repo_root,
            appsupport_root=appsupport_root,
            checkout_root=checkout_root,
            run_checks=False,
            provided_checks=provided_checks,
        )

        assert snapshot["where_we_are"]["repo"]["phase"] == "Ship"
        assert snapshot["where_we_are"]["appsupport"]["phase"] == "Plan"
        assert snapshot["where_we_are"]["repo"]["objective"] == "Wave19 live"
        assert snapshot["where_we_are"]["appsupport"]["objective"] == "Intake evozina"
        assert snapshot["dual_root"]["state_drift"] is True
        assert snapshot["dual_root"]["roadmap_drift"] is True
        assert "P0 wave19" in " ".join(snapshot["roadmap_next"]["repo"])
        assert "setup" in " ".join(snapshot["roadmap_next"]["appsupport"])

    print("OK: status report snapshot parsing verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
