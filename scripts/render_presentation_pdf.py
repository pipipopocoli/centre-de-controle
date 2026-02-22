#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QTextDocument
from PySide6.QtPrintSupport import QPrinter


def _default_projects_root() -> Path:
    # Canonical runtime root on macOS.
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _extract_md_bullets(md_text: str, header: str) -> list[str]:
    lines = md_text.splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == header
            continue
        if not in_section:
            continue
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if item:
                bullets.append(item)
        # stop if we hit another top-level heading
        if stripped.startswith("# "):
            break
    return bullets


def _read_project_state(project_id: str, projects_root: Path) -> tuple[str, str]:
    state_path = projects_root / project_id / "STATE.md"
    if not state_path.exists():
        return "Unknown", f"(missing {state_path})"
    text = state_path.read_text(encoding="utf-8", errors="replace")
    phase_items = _extract_md_bullets(text, "## Phase")
    obj_items = _extract_md_bullets(text, "## Objective")
    phase = phase_items[0] if phase_items else "Unknown"
    objective = " ".join(obj_items).strip() or "Unknown"
    return phase, objective


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render Cockpit presentation PDF from HTML template.")
    parser.add_argument("--project", default="cockpit", help="Project id to display in the PDF (default: cockpit)")
    parser.add_argument(
        "--projects-root",
        default="",
        help="Projects root override (default: macOS App Support root)",
    )
    parser.add_argument(
        "--html",
        default="docs/COCKPIT_PRESENTATION.html",
        help="HTML template path (default: docs/COCKPIT_PRESENTATION.html)",
    )
    parser.add_argument(
        "--out",
        default="docs/COCKPIT_PRESENTATION.pdf",
        help="Output PDF path (default: docs/COCKPIT_PRESENTATION.pdf)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    html_path = (repo_root / args.html).resolve()
    out_path = (repo_root / args.out).resolve()

    projects_root = Path(args.projects_root).expanduser().resolve() if args.projects_root else _default_projects_root()
    project_id = str(args.project).strip() or "cockpit"

    phase, objective = _read_project_state(project_id, projects_root)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not html_path.exists():
        raise FileNotFoundError(f"HTML template not found: {html_path}")

    template = html_path.read_text(encoding="utf-8", errors="replace")

    substitutions = {
        "{{PROJECT_ID}}": html.escape(project_id),
        "{{PHASE}}": html.escape(phase),
        "{{OBJECTIVE}}": html.escape(objective),
        "{{GENERATED_AT}}": html.escape(generated_at),
        "{{PROJECTS_ROOT}}": html.escape(str(projects_root)),
    }
    for key, value in substitutions.items():
        template = template.replace(key, value)

    app = QGuiApplication(sys.argv)
    doc = QTextDocument()
    doc.setBaseUrl(QUrl.fromLocalFile(str(repo_root) + "/"))
    doc.setHtml(template)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    printer = QPrinter()
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(out_path))
    printer.setResolution(300)

    doc.print_(printer)

    if not out_path.exists():
        raise RuntimeError("PDF render failed (file not created)")

    print(f"WROTE {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

