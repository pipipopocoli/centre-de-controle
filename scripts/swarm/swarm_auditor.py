from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover
    aiohttp = None

# Optional: load .env if python-dotenv is installed.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


DEFAULT_INCLUDE_EXT = (
    ".rs,.py,.ts,.tsx,.js,.jsx,.css,.md,.json,.toml,.yml,.yaml,.sh"
)

DEFAULT_IGNORE_DIRS = [
    ".git",
    "node_modules",
    "target",
    "build",
    "dist",
    "__pycache__",
    "venv",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

DEFAULT_IGNORE_PREFIXES = [
    "control/",
    "docs/swarm/",  # avoid auditing our own outputs by default
]

DEFAULT_MODEL_FILE = "google/gemini-2.5-flash-lite-preview-02-05:free"
DEFAULT_MODEL_SUMMARY = "openai/gpt-4o-mini"


SYSTEM_PROMPT_V2 = """You are Swarm Auditor v2. You analyze ONE repository file and output ONLY strict JSON.

Hard rules:
- ASCII only in ALL string fields. No emojis. No fancy quotes.
- Output MUST be a single JSON object. No markdown. No code fences.
- Max 8 issues per file.
- Be concrete and actionable. Prefer small diffs.
- Only include diff_unified if:
  - change is local to THIS file only
  - <= 40 changed lines (added+removed, excluding diff headers)
  - <= 200 total diff lines
  - unified diff format with correct file path headers:
    --- a/<file>
    +++ b/<file>
  Otherwise omit diff_unified and describe steps in detail.

Schema (v2):
{
  "issues": [
    {
      "severity": "p0|p1|p2|p3",
      "category": "bug|types|arch|ux|build|tests|perf|security|docs",
      "title": "short",
      "detail": "actionable, ascii",
      "questions": ["optional, ascii"],
      "diff_unified": "optional unified diff"
    }
  ],
  "file_questions": ["optional, ascii"],
  "notes": "optional, ascii"
}
"""

JSON_OBJECT_RESPONSE_FORMAT: dict[str, Any] = {"type": "json_object"}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_ascii(s: Any) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    # Keep it readable: replace non-ascii with '?'.
    return s.encode("ascii", "replace").decode("ascii")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_csv_ext(value: str) -> set[str]:
    exts: set[str] = set()
    for raw in (value or "").split(","):
        part = raw.strip()
        if not part:
            continue
        if not part.startswith("."):
            part = "." + part
        exts.add(part.lower())
    return exts


def _is_ignored_dirname(dirname: str, ignored: set[str]) -> bool:
    if dirname in ignored:
        return True
    # Any directory starting with ".venv" is ignored.
    if dirname.startswith(".venv"):
        return True
    return False


def _gather_files(
    *,
    repo_root: Path,
    include_ext: set[str],
    ignore_dir_names: set[str],
    ignore_prefixes: list[str],
) -> list[Path]:
    out: list[Path] = []
    repo_root = repo_root.resolve()

    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        rel_root = root_path.relative_to(repo_root).as_posix()
        if rel_root != ".":
            rel_root_slash = rel_root + "/"
            if any(rel_root_slash.startswith(p) for p in ignore_prefixes):
                dirs[:] = []
                continue

        # Prune ignored directories early.
        pruned: list[str] = []
        for d in dirs:
            if _is_ignored_dirname(d, ignore_dir_names):
                pruned.append(d)
        for d in pruned:
            dirs.remove(d)

        for fname in files:
            path = root_path / fname
            try:
                rel = path.relative_to(repo_root).as_posix()
            except Exception:
                continue

            if any(rel.startswith(p) for p in ignore_prefixes):
                continue

            ext = path.suffix.lower()
            if ext not in include_ext:
                continue

            out.append(path)

    out.sort(key=lambda p: p.as_posix())
    return out


def _sanitize_file_text(text: str) -> str:
    # Avoid markdown/codefence confusion in model outputs.
    return text.replace("```", "<<<CODE_FENCE>>>")


def _chunk_text(text: str, *, chunk_size: int = 8000, max_chunks: int = 4) -> tuple[list[str], bool]:
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    if len(chunks) <= max_chunks:
        return chunks, False
    return chunks[:max_chunks], True


def _make_user_content(relpath: str, text: str) -> tuple[str, str]:
    sanitized = _sanitize_file_text(text)
    chunks, truncated = _chunk_text(sanitized)
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"BEGIN_FILE {relpath} CHUNK {i}/{len(chunks)}")
        parts.append(chunk)
        parts.append("END_FILE")
    notes = ""
    if truncated:
        notes = "too_large: content truncated to 4 chunks"
    return "\n".join(parts), notes


def _rewrite_diff_paths(diff: str, relpath: str) -> str:
    lines = diff.splitlines()
    out: list[str] = []
    for ln in lines:
        if ln.startswith("--- "):
            out.append(f"--- a/{relpath}")
            continue
        if ln.startswith("+++ "):
            out.append(f"+++ b/{relpath}")
            continue
        out.append(ln)
    return "\n".join(out).rstrip() + "\n"


def _diff_changed_lines_count(diff: str) -> int:
    changed = 0
    for ln in diff.splitlines():
        if ln.startswith(("+++ ", "--- ", "@@")):
            continue
        if ln.startswith("+") or ln.startswith("-"):
            changed += 1
    return changed


def _diff_total_lines(diff: str) -> int:
    return len(diff.splitlines())


def _normalize_audit_payload(
    payload: Any, *, relpath: str, model: str, notes_hint: str = ""
) -> dict[str, Any]:
    audit: dict[str, Any] = {"issues": [], "file_questions": [], "notes": ""}
    if isinstance(payload, dict):
        audit["notes"] = _to_ascii(payload.get("notes", ""))[:2000]
        fq = payload.get("file_questions", [])
        if isinstance(fq, list):
            audit["file_questions"] = [_to_ascii(x)[:500] for x in fq][:50]

        issues = payload.get("issues", [])
        if isinstance(issues, list):
            for raw_issue in issues[:8]:
                if not isinstance(raw_issue, dict):
                    continue
                sev = _to_ascii(raw_issue.get("severity", "p2")).lower()
                if sev not in {"p0", "p1", "p2", "p3"}:
                    sev = "p2"
                cat = _to_ascii(raw_issue.get("category", "bug")).lower()
                if cat not in {"bug", "types", "arch", "ux", "build", "tests", "perf", "security", "docs"}:
                    cat = "bug"
                title = _to_ascii(raw_issue.get("title", "")).strip()[:120]
                detail = _to_ascii(raw_issue.get("detail", "")).strip()[:8000]

                q = raw_issue.get("questions", [])
                questions: list[str] = []
                if isinstance(q, list):
                    questions = [_to_ascii(x)[:500] for x in q][:20]

                diff = raw_issue.get("diff_unified", None)
                diff_out = None
                if isinstance(diff, str) and diff.strip():
                    diff_ascii = _to_ascii(diff)
                    diff_ascii = _rewrite_diff_paths(diff_ascii, relpath)
                    lines = diff_ascii.splitlines()
                    header_count = sum(1 for ln in lines if ln.startswith("--- "))
                    plus_count = sum(1 for ln in lines if ln.startswith("+++ "))
                    has_hunk = any(ln.startswith("@@") for ln in lines)
                    if (
                        header_count == 1
                        and plus_count == 1
                        and has_hunk
                        and _diff_total_lines(diff_ascii) <= 200
                        and _diff_changed_lines_count(diff_ascii) <= 40
                    ):
                        diff_out = diff_ascii

                issue_out: dict[str, Any] = {
                    "severity": sev,
                    "category": cat,
                    "title": title or "(missing title)",
                    "detail": detail or "(missing detail)",
                }
                if questions:
                    issue_out["questions"] = questions
                if diff_out is not None:
                    issue_out["diff_unified"] = diff_out
                audit["issues"].append(issue_out)

    if notes_hint:
        merged = (audit.get("notes") or "").strip()
        if merged:
            merged = merged + " | " + notes_hint
        else:
            merged = notes_hint
        audit["notes"] = merged[:2000]
        if "too_large" in notes_hint:
            fq = audit.get("file_questions", [])
            if not isinstance(fq, list):
                fq = []
            fq.append("File content was truncated; do we need a manual deep review for this file?")
            audit["file_questions"] = fq[:50]

    # Always ensure ASCII strings in audit tree.
    audit["notes"] = _to_ascii(audit.get("notes", ""))[:2000]
    audit["file_questions"] = [_to_ascii(x) for x in audit.get("file_questions", [])]
    for issue in audit.get("issues", []):
        issue["title"] = _to_ascii(issue.get("title", ""))[:120]
        issue["detail"] = _to_ascii(issue.get("detail", ""))[:8000]
        if "questions" in issue:
            issue["questions"] = [_to_ascii(x)[:500] for x in issue.get("questions", [])][:20]
        if "diff_unified" in issue:
            issue["diff_unified"] = _to_ascii(issue.get("diff_unified", ""))[:200000]

    return audit


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    base_url: str
    model: str


async def _openrouter_call_json(
    session: aiohttp.ClientSession,
    cfg: OpenRouterConfig,
    *,
    system_prompt: str,
    user_content: str,
    response_format: dict[str, Any] | None = JSON_OBJECT_RESPONSE_FORMAT,
    timeout_total_s: int = 90,
) -> tuple[int, str, dict[str, Any] | None]:
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "HTTP-Referer": "https://cockpit.local",
        "X-Title": "Cockpit Swarm Auditor v2",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    timeout = aiohttp.ClientTimeout(total=timeout_total_s, connect=10, sock_read=60)
    async with session.post(url, headers=headers, json=payload, timeout=timeout) as resp:
        text = await resp.text()
        if resp.status != 200:
            return resp.status, text, None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return resp.status, text, None
        return resp.status, text, data


async def _audit_one_file(
    *,
    sem: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    or_cfg: OpenRouterConfig,
    repo_root: Path,
    path: Path,
    cache_index: dict[str, Any],
    use_cache: bool,
    resume: bool,
) -> dict[str, Any]:
    relpath = path.relative_to(repo_root).as_posix()
    started = time.monotonic()

    try:
        data_bytes = path.read_bytes()
    except Exception as e:
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "exception",
            "model": or_cfg.model,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": "",
            "audit": {
                "issues": [
                    {
                        "severity": "p1",
                        "category": "build",
                        "title": "cannot read file",
                        "detail": _to_ascii(str(e)),
                    }
                ],
                "file_questions": [],
                "notes": "exception",
            },
        }

    sha = _sha256_bytes(data_bytes)
    try:
        text = data_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Best effort for configs; replace invalid bytes.
        text = data_bytes.decode("utf-8", errors="replace")

    if len(text.strip()) < 10:
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "skipped",
            "model": or_cfg.model,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": sha,
            "audit": {"issues": [], "file_questions": [], "notes": "too_short"},
        }

    if use_cache and resume and sha in cache_index:
        cached = cache_index[sha]
        audit = _normalize_audit_payload(cached.get("audit", {}), relpath=relpath, model=or_cfg.model, notes_hint="cached")
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "cached",
            "model": cached.get("model", or_cfg.model),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": sha,
            "audit": audit,
        }

    user_content, notes_hint = _make_user_content(relpath, text)

    async with sem:
        # Retry policy:
        # - 429: exponential backoff + jitter, max 6 retries
        # - 5xx/timeout: max 3 retries
        rate_retries = 6
        transient_retries = 3

        attempt = 0
        last_status = 0
        last_text = ""
        while True:
            attempt += 1
            try:
                status, resp_text, data = await _openrouter_call_json(
                    session, or_cfg, system_prompt=SYSTEM_PROMPT_V2, user_content=user_content
                )
                last_status = status
                last_text = resp_text
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                transient_retries -= 1
                if transient_retries < 0:
                    return {
                        "schema_version": 2,
                        "file": relpath,
                        "status": "http_error",
                        "model": or_cfg.model,
                        "elapsed_ms": int((time.monotonic() - started) * 1000),
                        "content_sha256": sha,
                        "audit": {
                            "issues": [
                                {
                                    "severity": "p1",
                                    "category": "build",
                                    "title": "openrouter request failed",
                                    "detail": _to_ascii(str(e)),
                                }
                            ],
                            "file_questions": [],
                            "notes": "http_error",
                        },
                    }
                await asyncio.sleep(0.5 * (2**attempt) + random.random() * 0.25)
                continue

            if status == 429:
                rate_retries -= 1
                if rate_retries < 0:
                    return {
                        "schema_version": 2,
                        "file": relpath,
                        "status": "rate_limited",
                        "model": or_cfg.model,
                        "elapsed_ms": int((time.monotonic() - started) * 1000),
                        "content_sha256": sha,
                        "audit": {
                            "issues": [
                                {
                                    "severity": "p1",
                                    "category": "build",
                                    "title": "rate limited by openrouter",
                                    "detail": "HTTP 429 after retries",
                                    "questions": [
                                        "Should we lower --max-concurrency or switch model?",
                                    ],
                                }
                            ],
                            "file_questions": [],
                            "notes": "rate_limited",
                        },
                    }
                backoff = min(30.0, 0.75 * (2**attempt) + random.random())
                await asyncio.sleep(backoff)
                continue

            if 500 <= status <= 599:
                transient_retries -= 1
                if transient_retries < 0:
                    return {
                        "schema_version": 2,
                        "file": relpath,
                        "status": "http_error",
                        "model": or_cfg.model,
                        "elapsed_ms": int((time.monotonic() - started) * 1000),
                        "content_sha256": sha,
                        "audit": {
                            "issues": [
                                {
                                    "severity": "p1",
                                    "category": "build",
                                    "title": "openrouter server error",
                                    "detail": f"HTTP {status}",
                                }
                            ],
                            "file_questions": [],
                            "notes": "http_error",
                        },
                    }
                await asyncio.sleep(0.5 * (2**attempt) + random.random() * 0.25)
                continue

            break

    # Parse content from successful or non-200 responses.
    if last_status != 200:
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "http_error",
            "model": or_cfg.model,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": sha,
            "audit": {
                "issues": [
                    {
                        "severity": "p1",
                        "category": "build",
                        "title": "openrouter http error",
                        "detail": f"HTTP {last_status}: {_to_ascii(last_text)[:500]}",
                    }
                ],
                "file_questions": [],
                "notes": "http_error",
            },
        }

    try:
        outer = json.loads(last_text)
        content = outer["choices"][0]["message"]["content"]
    except Exception as e:
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "parse_error",
            "model": or_cfg.model,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": sha,
            "audit": {
                "issues": [
                    {
                        "severity": "p2",
                        "category": "docs",
                        "title": "unexpected openrouter response shape",
                        "detail": _to_ascii(str(e))[:500],
                        "questions": [
                            "Is OpenRouter returning a different schema for this model?",
                        ],
                    }
                ],
                "file_questions": [],
                "notes": "parse_error",
            },
            "raw_text": _to_ascii(last_text)[:4000],
        }

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {
            "schema_version": 2,
            "file": relpath,
            "status": "parse_error",
            "model": or_cfg.model,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_sha256": sha,
            "audit": {
                "issues": [
                    {
                        "severity": "p2",
                        "category": "docs",
                        "title": "model did not return valid json",
                        "detail": "Could not parse message content as JSON.",
                        "questions": [
                            "Should we switch to a model with stronger JSON adherence?",
                        ],
                    }
                ],
                "file_questions": [],
                "notes": "parse_error",
            },
            "raw_text": _to_ascii(content)[:4000],
        }

    audit = _normalize_audit_payload(parsed, relpath=relpath, model=or_cfg.model, notes_hint=notes_hint)
    entry = {
        "schema_version": 2,
        "file": relpath,
        "status": "success",
        "model": or_cfg.model,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "content_sha256": sha,
        "audit": audit,
    }

    if use_cache:
        cache_index[sha] = {
            "model": or_cfg.model,
            "audit": audit,
            "cached_at": _now_utc_iso(),
        }

    return entry


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _make_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand = f"{random.randint(0, 9999):04d}"
    return f"{ts}_{rand}"


async def _run_async(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    include_ext = _parse_csv_ext(args.include_ext)

    ignore_dir_names = set(DEFAULT_IGNORE_DIRS)
    for d in args.ignore_dir or []:
        ignore_dir_names.add(d)

    ignore_prefixes = list(DEFAULT_IGNORE_PREFIXES)
    for p in args.ignore_prefix or []:
        p2 = p.strip().replace("\\", "/")
        if p2 and not p2.endswith("/"):
            # Prefix match is clearer with trailing slash.
            if not Path(p2).suffix:
                p2 = p2 + "/"
        ignore_prefixes.append(p2)

    # Always ignore our out_dir relative path if it lives under repo_root.
    try:
        rel_out = out_dir.relative_to(repo_root).as_posix()
        if rel_out and rel_out != ".":
            if not rel_out.endswith("/"):
                rel_out = rel_out + "/"
            if rel_out not in ignore_prefixes:
                ignore_prefixes.append(rel_out)
    except Exception:
        pass

    files = _gather_files(
        repo_root=repo_root,
        include_ext=include_ext,
        ignore_dir_names=ignore_dir_names,
        ignore_prefixes=ignore_prefixes,
    )
    if getattr(args, "limit", 0):
        try:
            lim = int(args.limit)
        except Exception:
            lim = 0
        if lim > 0:
            files = files[:lim]

    if args.dry_run:
        for p in files:
            print(p.relative_to(repo_root).as_posix())
        print(f"files_total={len(files)}")
        return 0

    if aiohttp is None:
        print(
            "ERROR: missing dependency 'aiohttp'. Install deps with: python3 -m pip install -r scripts/swarm/requirements_swarm.txt",
            file=sys.stderr,
        )
        return 2

    api_key = os.getenv("COCKPIT_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""
    if not api_key:
        print("ERROR: COCKPIT_OPENROUTER_API_KEY is not set (required unless --dry-run).", file=sys.stderr)
        return 2

    base_url = os.getenv("COCKPIT_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    or_cfg = OpenRouterConfig(api_key=api_key, base_url=base_url, model=args.model_file)

    run_id = _make_run_id()
    run_dir = out_dir / "_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_index_path = cache_dir / "index.json"
    cache_index: dict[str, Any] = {}
    if args.cache:
        loaded = _load_json_file(cache_index_path)
        if isinstance(loaded, dict):
            cache_index = loaded

    meta = {
        "schema_version": 2,
        "run_id": run_id,
        "started_at": _now_utc_iso(),
        "repo_root": repo_root.as_posix(),
        "out_dir": out_dir.as_posix(),
        "include_ext": sorted(include_ext),
        "ignore_dir": sorted(ignore_dir_names),
        "ignore_prefix": ignore_prefixes,
        "max_concurrency": args.max_concurrency,
        "model_file": args.model_file,
        "model_summary": args.model_summary,
        "cache": bool(args.cache),
        "resume": bool(args.resume),
        "emit_patch_file": bool(args.emit_patch_file),
        "consolidate": bool(args.consolidate),
    }
    _write_json_file(run_dir / "meta.json", meta)

    raw_path = run_dir / "raw.ndjson"
    write_lock = asyncio.Lock()

    connector = aiohttp.TCPConnector(limit=max(1, int(args.max_concurrency)))
    async with aiohttp.ClientSession(connector=connector) as session:
        sem = asyncio.Semaphore(max(1, int(args.max_concurrency)))

        processed = 0
        total = len(files)
        worker_count = max(1, int(args.max_concurrency))
        q: asyncio.Queue[Path | None] = asyncio.Queue()
        for p in files:
            q.put_nowait(p)
        for _ in range(worker_count):
            q.put_nowait(None)

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open("a", encoding="utf-8") as raw_file:

            async def worker() -> None:
                nonlocal processed
                while True:
                    p = await q.get()
                    try:
                        if p is None:
                            return
                        entry = await _audit_one_file(
                            sem=sem,
                            session=session,
                            or_cfg=or_cfg,
                            repo_root=repo_root,
                            path=p,
                            cache_index=cache_index,
                            use_cache=bool(args.cache),
                            resume=bool(args.resume),
                        )
                        line = json.dumps(entry, ensure_ascii=True)
                        async with write_lock:
                            raw_file.write(line + "\n")
                            raw_file.flush()
                        processed += 1
                        if processed % 25 == 0 or processed == total:
                            print(f"progress {processed}/{total}")
                    finally:
                        q.task_done()

            tasks = [asyncio.create_task(worker()) for _ in range(worker_count)]
            await q.join()
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    if args.cache:
        _write_json_file(cache_index_path, cache_index)

    meta["finished_at"] = _now_utc_iso()
    meta["files_total"] = len(files)
    meta["raw_ndjson"] = raw_path.as_posix()
    _write_json_file(run_dir / "meta.json", meta)

    # Consolidation (default ON).
    if args.consolidate:
        cmd = [
            sys.executable,
            str((repo_root / "scripts" / "swarm" / "swarm_consolidator.py").resolve()),
            "--in",
            str(raw_path),
            "--out-dir",
            str(out_dir),
        ]
        if args.emit_patch_file:
            cmd.append("--emit-patch-file")
        # Keep patch check optional in consolidator only.
        print("running consolidator...")
        subprocess.run(cmd, check=False)

    # Big push summary (best effort, non-blocking).
    try:
        await _generate_big_push_summary(
            out_dir=out_dir,
            repo_root=repo_root,
            api_key=api_key,
            base_url=base_url,
            model=args.model_summary,
        )
    except Exception as e:
        print(f"summary failed: {_to_ascii(e)}", file=sys.stderr)

    print(f"run_id={run_id}")
    print(f"raw_ndjson={raw_path.as_posix()}")
    return 0


async def _generate_big_push_summary(
    *,
    out_dir: Path,
    repo_root: Path,
    api_key: str,
    base_url: str,
    model: str,
) -> None:
    summary_path = out_dir / "latest_summary.json"
    questions_path = out_dir / "latest_questions.md"
    report_path = out_dir / "latest_report.md"

    summary = _load_json_file(summary_path)
    if not isinstance(summary, dict):
        return

    issues = summary.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    # Pull questions from latest_questions.md (deterministic, already deduped).
    q_text = ""
    if questions_path.exists():
        q_text = questions_path.read_text(encoding="utf-8", errors="replace")

    stats = summary.get("stats", {})
    stats_text = _to_ascii(json.dumps(stats, sort_keys=True))[:4000]

    top_issues = []
    for it in issues[:50]:
        if not isinstance(it, dict):
            continue
        top_issues.append(
            {
                "file": _to_ascii(it.get("file", "")),
                "severity": _to_ascii(it.get("severity", "")),
                "category": _to_ascii(it.get("category", "")),
                "title": _to_ascii(it.get("title", "")),
                "detail": _to_ascii(it.get("detail", ""))[:600],
            }
        )

    user_content = "\n".join(
        [
            "You are Swarm Consolidation Lead. Produce a single markdown document (ASCII only).",
            "",
            "Goal: propose a big push plan in at most 5 PRs, each PR small, testable, reversible.",
            "Include:",
            "- Proposed PR list (<=5) with scope and acceptance checks",
            "- Owners suggestion (victor/leo/nova/clems) where it fits",
            "- Top risks and mitigations",
            "- Blocking questions (deduped)",
            "",
            "Repo stats JSON:",
            stats_text,
            "",
            "Top issues (JSON array):",
            _to_ascii(json.dumps(top_issues, indent=2)),
            "",
            "Questions markdown (already deduped):",
            _to_ascii(q_text)[:8000],
            "",
            "If report exists, use it for context but do not quote it verbatim.",
        ]
    )

    or_cfg = OpenRouterConfig(api_key=api_key, base_url=base_url, model=model)
    connector = aiohttp.TCPConnector(limit=4)
    async with aiohttp.ClientSession(connector=connector) as session:
        status, resp_text, data = await _openrouter_call_json(
            session,
            or_cfg,
            system_prompt="You output only markdown. ASCII only. No code fences.",
            user_content=user_content,
            response_format=None,
            timeout_total_s=120,
        )
        if status != 200 or data is None:
            return
        try:
            outer = json.loads(resp_text)
            content = outer["choices"][0]["message"]["content"]
        except Exception:
            return

    out = _to_ascii(content).strip() + "\n"
    (out_dir / "latest_big_push.md").write_text(out, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Swarm Auditor v2 (issues + questions + diffs)")

    parser.add_argument("--dry-run", action="store_true", help="List files only. No API calls.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files (smoke test). Default: 0 (no limit).")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent), help="Repo root path.")
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent.parent / "docs" / "swarm"))
    parser.add_argument("--max-concurrency", type=int, default=10)
    parser.add_argument("--model-file", default=DEFAULT_MODEL_FILE)
    parser.add_argument("--model-summary", default=DEFAULT_MODEL_SUMMARY)
    parser.add_argument("--include-ext", default=DEFAULT_INCLUDE_EXT)

    parser.add_argument("--ignore-dir", action="append", default=[], help="Repeatable. Directory name to ignore.")
    parser.add_argument("--ignore-prefix", action="append", default=[], help="Repeatable. Relative path prefix to ignore.")

    parser.add_argument(
        "--cache",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable cache. Default: enabled.",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable resume via cache. Default: enabled.",
    )
    parser.add_argument("--emit-patch-file", action="store_true", help="Emit combined patch in docs/swarm/latest_diffs.patch")
    parser.add_argument(
        "--consolidate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run consolidator at end. Default: enabled.",
    )

    args = parser.parse_args()

    try:
        rc = asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        rc = 130
    sys.exit(rc)


if __name__ == "__main__":
    main()
