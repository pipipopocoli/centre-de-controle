#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Cockpit cloud API server (Desktop + Android).")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8100, help="Bind port (default: 8100).")
    parser.add_argument(
        "--projects-root",
        default="",
        help="Override projects root (default: ~/Library/Application Support/Cockpit/projects).",
    )
    args = parser.parse_args()

    if args.projects_root:
        os.environ["COCKPIT_API_PROJECTS_ROOT"] = args.projects_root

    if not str(os.environ.get("COCKPIT_OPENROUTER_API_KEY") or "").strip():
        raise SystemExit("Missing required env: COCKPIT_OPENROUTER_API_KEY")
    uvicorn.run("server.main:app", host=args.host, port=max(args.port, 1), reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
