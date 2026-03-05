"""Direct OpenRouter LLM chat service for the Cockpit desktop app.

Provides a conversational AI assistant (Clems) that maintains multi-turn
conversation history and responds via the OpenRouter API.

This module is self-contained and does NOT import from the ``server`` package
to avoid triggering heavy pydantic/starlette dependencies.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from typing import Any, Callable


_ENV_API_KEY = "COCKPIT_OPENROUTER_API_KEY"
_ENV_MODEL = "COCKPIT_MODEL_CHAT"
_ENV_BASE_URL = "COCKPIT_OPENROUTER_BASE_URL"

_DEFAULT_MODEL = "openai/gpt-4o-mini"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

MAX_HISTORY = 30  # Keep last N messages for context

SYSTEM_PROMPT = (
    "Tu es Clems, l'orchestrateur IA du Centre de Controle (Cockpit). "
    "Tu assistes l'operateur en francais. Tu es direct, concis et utile. "
    "Tu connais le projet, les agents (Victor=backend, Leo=UI, Nova=research, Vulgarisation=docs). "
    "Reponds de maniere conversationnelle comme un coequipier. "
    "Si on te pose une question technique, donne une reponse claire et actionnable. "
    "Utilise des emojis avec parcimonie pour rester professionnel mais friendly."
)


def _get_api_key() -> str:
    return str(os.environ.get(_ENV_API_KEY) or "").strip()


def _get_model() -> str:
    return str(os.environ.get(_ENV_MODEL) or _DEFAULT_MODEL).strip()


def _get_base_url() -> str:
    return str(os.environ.get(_ENV_BASE_URL) or _DEFAULT_BASE_URL).strip()


# ── Lightweight OpenRouter HTTP client (avoids server package imports) ──

def _openrouter_chat(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.7,
    timeout_seconds: int = 60,
) -> str:
    """Send a chat completion request to OpenRouter and return the text."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": max(min(float(temperature), 2.0), 0.0),
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "HTTP-Referer": "https://cockpit.local",
        "X-Title": "Cockpit",
    }
    request = urllib.request.Request(url=url, method="POST", headers=headers, data=data)

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="ignore").strip()[:200]
        except Exception:
            pass
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter unreachable: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenRouter returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("OpenRouter returned unexpected response type")

    # Extract text from choices
    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        return "\n".join(chunks).strip()
    return ""


# ── Conversation history ──────────────────────────────────────────────

class ChatHistory:
    """Thread-safe conversation history."""

    def __init__(self, max_messages: int = MAX_HISTORY) -> None:
        self._messages: list[dict[str, str]] = []
        self._max = max_messages
        self._lock = threading.Lock()

    def add_user(self, text: str) -> None:
        with self._lock:
            self._messages.append({"role": "user", "content": text})
            self._trim()

    def add_assistant(self, text: str) -> None:
        with self._lock:
            self._messages.append({"role": "assistant", "content": text})
            self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        with self._lock:
            return list(self._messages)

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()

    def _trim(self) -> None:
        if len(self._messages) > self._max:
            self._messages = self._messages[-self._max:]


# Module-level singleton for conversation history
_history = ChatHistory()


def get_history() -> ChatHistory:
    return _history


def reset_history() -> None:
    _history.clear()


def send_message_sync(user_text: str, *, project_context: str = "") -> str:
    """Send a message to the LLM and get a response synchronously.

    Args:
        user_text: The operator's message.
        project_context: Optional project state summary to inject.

    Returns:
        The AI assistant's response text, or an error message.
    """
    api_key = _get_api_key()
    if not api_key:
        return (
            "⚠️ Clé API OpenRouter manquante. "
            "Configure COCKPIT_OPENROUTER_API_KEY pour activer le chat IA."
        )

    _history.add_user(user_text)

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if project_context:
        messages.append({
            "role": "system",
            "content": f"Contexte projet actuel:\n{project_context}",
        })
    messages.extend(_history.get_messages())

    model = _get_model()
    base_url = _get_base_url()

    try:
        result = _openrouter_chat(
            api_key=api_key,
            base_url=base_url,
            model=model,
            messages=messages,
            temperature=0.7,
        )
    except Exception as exc:
        error_msg = f"⚠️ Erreur LLM: {exc}"
        _history.add_assistant(error_msg)
        return error_msg

    if not result:
        error_msg = "⚠️ LLM a retourné une réponse vide"
        _history.add_assistant(error_msg)
        return error_msg

    _history.add_assistant(result)
    return result


def send_message_async(
    user_text: str,
    *,
    project_context: str = "",
    on_success: Callable[[str], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> threading.Thread:
    """Send a message to the LLM in a background thread.

    Callbacks are called from the worker thread — use Qt signals to
    marshal back to the main thread.
    """
    def _worker() -> None:
        try:
            response = send_message_sync(user_text, project_context=project_context)
            if on_success:
                on_success(response)
        except Exception as exc:
            if on_error:
                on_error(str(exc))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
