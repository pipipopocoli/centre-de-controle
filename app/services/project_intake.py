from __future__ import annotations

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


def scan_repo(repo_path: Path) -> dict[str, Any]:
    repo_path = repo_path.expanduser().resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"Repo path not found: {repo_path}")

    files_scanned = 0
    ext_counts: Counter[str] = Counter()
    configs: set[str] = set()
    top_files: list[str] = []
    readme_excerpt = _read_readme(repo_path)

    for path in repo_path.rglob("*"):
        if files_scanned >= MAX_FILES:
            break
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.is_dir():
            continue
        files_scanned += 1
        if path.name in CONFIG_FILES:
            configs.add(path.name)
        if path.suffix:
            ext_counts[path.suffix.lower()] += 1
        if len(top_files) < 30:
            top_files.append(str(path.relative_to(repo_path)))

    stack = _detect_stack(configs, ext_counts)
    languages = [f"{ext} ({count})" for ext, count in ext_counts.most_common(8)]

    risks: list[str] = []
    if not readme_excerpt:
        risks.append("No README found (context may be missing)")
    if "tests" not in {p.lower() for p in top_files}:
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
