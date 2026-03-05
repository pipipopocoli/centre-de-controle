from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RunnerResult:
    runner: str
    status: str
    success: bool
    launched: bool
    completed: bool
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None
    started_at: str
    finished_at: str
    duration_seconds: float
    output_path: str | None
    output_text: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _resolve_api_key() -> str:
    key = str(os.environ.get("COCKPIT_OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("openrouter_api_key_missing")
    return key


def _resolve_base_url() -> str:
    return str(os.environ.get("COCKPIT_OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")


def _resolve_model() -> str:
    return str(
        os.environ.get("COCKPIT_OPENROUTER_MODEL")
        or os.environ.get("COCKPIT_MODEL_L1")
        or "moonshotai/kimi-k2.5"
    ).strip()


def _extract_message_content(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()
    return ""


def _chat_completion(prompt: str, *, timeout_s: int) -> tuple[str, str]:
    key = _resolve_api_key()
    base_url = _resolve_base_url()
    model = _resolve_model()

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=max(int(timeout_s), 30)) as response:
        raw = response.read().decode("utf-8", errors="replace")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("openrouter_invalid_payload")
    content = _extract_message_content(payload)
    if not content:
        raise RuntimeError("openrouter_empty_content")
    return content, raw


def run_openrouter(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    output_path: Path | None = None,
) -> RunnerResult:
    started_at = _utc_now_iso()
    started_mono = time.monotonic()

    managed_output = output_path is None
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(prefix="cockpit_openrouter_", suffix=".txt", delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_text, raw_json = _chat_completion(prompt, timeout_s=timeout_s)
        output_path.write_text(output_text, encoding="utf-8")
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="completed",
            success=True,
            launched=True,
            completed=True,
            returncode=0,
            stdout="openrouter_api_call_ok",
            stderr="",
            error=None,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text=output_text,
        )
    except urllib.error.HTTPError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        error = f"openrouter_http_error:{exc.code}"
        if body:
            error = f"{error}:{body.strip()}"
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=True,
            completed=True,
            returncode=exc.code,
            stdout="",
            stderr=body.strip(),
            error=error,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    except urllib.error.URLError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"openrouter_network_error:{exc}",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    except TimeoutError:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="timeout",
            success=False,
            launched=True,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"openrouter timeout after {max(int(timeout_s), 30)}s",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    except Exception as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=str(exc),
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_path),
            output_text="",
        )
    finally:
        if managed_output and output_path is not None:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass


def run_openrouter_exec(
    prompt: str,
    cwd: Path,
    timeout_s: int,
    *,
    sandbox_mode: str = "read-only",
    approval_policy: str = "never",
    output_schema_path: Path | None = None,
    output_last_message_path: Path | None = None,
    ephemeral: bool = True,
) -> RunnerResult:
    _ = (cwd, sandbox_mode, approval_policy, ephemeral)
    started_at = _utc_now_iso()
    started_mono = time.monotonic()

    managed_output = output_last_message_path is None
    if output_last_message_path is None:
        tmp = tempfile.NamedTemporaryFile(prefix="cockpit_openrouter_exec_", suffix=".json", delete=False)
        output_last_message_path = Path(tmp.name)
        tmp.close()
    else:
        output_last_message_path = Path(output_last_message_path)
        output_last_message_path.parent.mkdir(parents=True, exist_ok=True)

    schema_instruction = ""
    if output_schema_path is not None:
        output_schema_path = Path(output_schema_path)
        if output_schema_path.exists():
            schema_text = _read_text(output_schema_path)
            if schema_text:
                schema_instruction = (
                    "\n\nOutput requirements:\n"
                    "- Return only valid JSON.\n"
                    "- Match this JSON schema exactly:\n"
                    f"{schema_text}\n"
                )

    full_prompt = f"{prompt}{schema_instruction}" if schema_instruction else prompt

    try:
        output_text, _raw_json = _chat_completion(full_prompt, timeout_s=timeout_s)
        output_last_message_path.write_text(output_text, encoding="utf-8")
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="completed",
            success=True,
            launched=True,
            completed=True,
            returncode=0,
            stdout="openrouter_api_call_ok",
            stderr="",
            error=None,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_last_message_path),
            output_text=output_text,
        )
    except urllib.error.HTTPError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        error = f"openrouter_http_error:{exc.code}"
        if body:
            error = f"{error}:{body.strip()}"
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=True,
            completed=True,
            returncode=exc.code,
            stdout="",
            stderr=body.strip(),
            error=error,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_last_message_path),
            output_text="",
        )
    except urllib.error.URLError as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"openrouter_network_error:{exc}",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_last_message_path),
            output_text="",
        )
    except TimeoutError:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="timeout",
            success=False,
            launched=True,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"openrouter timeout after {max(int(timeout_s), 30)}s",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_last_message_path),
            output_text="",
        )
    except Exception as exc:
        duration = max(time.monotonic() - started_mono, 0.0)
        return RunnerResult(
            runner="openrouter",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=str(exc),
            started_at=started_at,
            finished_at=_utc_now_iso(),
            duration_seconds=round(duration, 3),
            output_path=str(output_last_message_path),
            output_text="",
        )
    finally:
        if managed_output and output_last_message_path is not None:
            try:
                output_last_message_path.unlink(missing_ok=True)
            except OSError:
                pass
