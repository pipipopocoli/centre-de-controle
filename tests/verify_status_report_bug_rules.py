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
            "from __future__ import annotations\n"
            "import shutil\n\n"
            "def _boot_cleanup():\n"
            "    for folder in ['runs', 'chat', 'agents', 'vulgarisation']:\n"
            "        shutil.rmtree(folder, ignore_errors=True)\n",
        )
        _write(
            checkout_root / "docs" / "WIZARD_LIVE.md",
            "# Wizard Live\n\n- Voice: hors scope Wave19 (texte only)\n",
        )
        _write(checkout_root / "scripts" / "export_status_pdf.py", "# marker\n")

        _write(repo_root / "STATE.md", "# State\n\n## Phase\n- Ship\n")
        _write(appsupport_root / "STATE.md", "# State\n\n## Phase\n- Plan\n")
        _write(repo_root / "ROADMAP.md", "# Roadmap\n\n## Next wave entrypoint\n- run wave19\n")
        _write(appsupport_root / "ROADMAP.md", "# Roadmap\n\n## Next\n- intake\n")
        _write(repo_root / "DECISIONS.md", "# Decisions\n\n## ADR-1\n- Accepted\n")
        _write(appsupport_root / "DECISIONS.md", "# Decisions\n\n## ADR-2\n- Accepted\n")
        (repo_root / "runs").mkdir(parents=True, exist_ok=True)
        (appsupport_root / "runs").mkdir(parents=True, exist_ok=True)

        provided_checks = {
            "tests": [
                {
                    "name": "tests/verify_codex_runner.py",
                    "command": "python tests/verify_codex_runner.py",
                    "returncode": 1,
                    "ok": False,
                    "stdout": "",
                    "stderr": "AssertionError: result.success is True",
                }
            ],
            "scripts": [
                {
                    "name": "scripts/render_presentation_pdf.py",
                    "command": "python scripts/render_presentation_pdf.py --project cockpit",
                    "returncode": 1,
                    "ok": False,
                    "stdout": "",
                    "stderr": "FileNotFoundError: HTML template not found",
                }
            ],
        }

        snapshot = collect_status_snapshot(
            project_id="cockpit",
            repo_root=repo_root,
            appsupport_root=appsupport_root,
            checkout_root=checkout_root,
            run_checks=False,
            provided_checks=provided_checks,
        )

        bug_ids = {str(item.get("id") or "") for item in snapshot.get("bugs", [])}
        missing_ids = {str(item.get("id") or "") for item in snapshot.get("missing", [])}

        assert "codex_runner_contract" in bug_ids
        assert "destructive_boot_cleanup" in bug_ids
        assert "render_presentation_pdf_broken" in bug_ids
        assert "dual_root_drift" in bug_ids

        assert "wave19_live_evidence_missing" in missing_ids
        assert "dual_root_alignment_missing" in missing_ids
        assert "voice_pipeline_absent" in missing_ids

        assert snapshot.get("overall_status") == "blocked"

    print("OK: status report bug rules verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
