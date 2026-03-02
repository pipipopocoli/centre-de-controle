from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.status_report import render_pdf_from_html  # noqa: E402


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "status_report.pdf"
        html_content = """
<!doctype html>
<html lang="fr">
  <head><meta charset="utf-8"><title>test</title></head>
  <body>
    <h1>Rapport</h1>
    <p>Etat dual-root.</p>
  </body>
</html>
"""
        output = render_pdf_from_html(html_content, out_path)
        assert output.exists()
        assert output.stat().st_size > 0

    print("OK: status report pdf render verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
