from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
}

CONFIG_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Gemfile",
    "mix.exs",
}

README_FILES = {"README.md", "README.txt", "README"}

MAX_FILES = 2000
MAX_READ_BYTES = 200000
ONBOARDING_PACK_SCHEMA_VERSION = "wave16_onboarding_pack_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _detect_stack(configs: set[str], ext_counts: Counter) -> list[str]:
    stack: list[str] = []
    if {"pyproject.toml", "requirements.txt", "setup.cfg"} & configs:
        stack.append("python")
    if "package.json" in configs:
        stack.append("node")
    if "Cargo.toml" in configs:
        stack.append("rust")
    if "go.mod" in configs:
        stack.append("go")
    if "Gemfile" in configs:
        stack.append("ruby")
    if "composer.json" in configs:
        stack.append("php")
    if "mix.exs" in configs:
        stack.append("elixir")

    # Heuristic from extensions
    top_ext = {ext for ext, _count in ext_counts.most_common(5)}
    if ".py" in top_ext and "python" not in stack:
        stack.append("python")
    if {".js", ".ts"} & top_ext and "node" not in stack:
        stack.append("node")
    if ".rs" in top_ext and "rust" not in stack:
        stack.append("rust")
    if ".go" in top_ext and "go" not in stack:
        stack.append("go")
    if ".rb" in top_ext and "ruby" not in stack:
        stack.append("ruby")

    return stack or ["unknown"]


def _read_readme(repo_path: Path) -> str:
    for name in README_FILES:
        path = repo_path / name
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8", errors="ignore")
            return content[:MAX_READ_BYTES]
    return ""


def _iter_repo_files(repo_path: Path):
    repo_root = repo_path.expanduser().resolve()
    for current_root, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORE_DIRS)
        for filename in sorted(filenames):
            path = Path(current_root) / filename
            yield path


def scan_repo(repo_path: Path) -> dict[str, Any]:
    repo_path = repo_path.expanduser().resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"Repo path not found: {repo_path}")

    files_scanned = 0
    ext_counts: Counter[str] = Counter()
    configs: set[str] = set()
    top_files: list[str] = []
    readme_excerpt = _read_readme(repo_path)
    tests_detected = False

    for path in _iter_repo_files(repo_path):
        if files_scanned >= MAX_FILES:
            break
        files_scanned += 1

        relative = path.relative_to(repo_path)
        relative_text = str(relative)
        lower_parts = [part.lower() for part in relative.parts]
        if any(part in {"tests", "test"} for part in lower_parts):
            tests_detected = True

        if path.name in CONFIG_FILES:
            configs.add(path.name)
        if path.suffix:
            ext_counts[path.suffix.lower()] += 1
        if len(top_files) < 30:
            top_files.append(relative_text)

    top_files = sorted(top_files)

    stack = _detect_stack(configs, ext_counts)
    languages = [f"{ext} ({count})" for ext, count in ext_counts.most_common(8)]

    risks: list[str] = []
    if not readme_excerpt:
        risks.append("No README found (context may be missing)")
    if not tests_detected:
        risks.append("Tests folder not detected (QA may be unclear)")
    if len(stack) > 1 and "unknown" not in stack:
        risks.append("Multi-stack project (scope risk)")

    return {
        "project_name": repo_path.name,
        "repo_path": str(repo_path),
        "stack": stack,
        "languages": languages,
        "configs": sorted(configs),
        "top_files": top_files,
        "readme_excerpt": readme_excerpt[:2000],
        "risks": risks,
        "stats": {
            "files_scanned": files_scanned,
        },
        "scanned_at": _utc_now_iso(),
    }


def build_onboarding_pack(
    *,
    project_id: str,
    project_dir: Path,
    projects_root: Path,
    repo_path: Path,
    run_intake: bool,
    startup_pack_path: Path,
    issue_seed_paths: list[str] | None = None,
    command_path: str = "scripts/project_intake.py",
) -> dict[str, Any]:
    seeds = sorted(str(item).strip() for item in (issue_seed_paths or []) if str(item).strip())
    return {
        "schema_version": ONBOARDING_PACK_SCHEMA_VERSION,
        "project_id": str(project_id),
        "project_dir": str(project_dir),
        "projects_root": str(projects_root),
        "repo_path": str(repo_path),
        "run_intake": bool(run_intake),
        "startup_pack_path": str(startup_pack_path),
        "issue_seed_paths": seeds,
        "command_path": str(command_path),
    }


def write_onboarding_pack(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
