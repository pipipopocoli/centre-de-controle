from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenRouterUsage:
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    raw: dict[str, Any]


@dataclass(frozen=True)
class OpenRouterChatResult:
    status: str
    model: str
    text: str
    usage: OpenRouterUsage
    raw: dict[str, Any]
    error: str | None = None


def _safe_int(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _parse_usage(payload: dict[str, Any]) -> OpenRouterUsage:
    usage_raw = payload.get("usage")
    usage = usage_raw if isinstance(usage_raw, dict) else {}
    input_tokens = _safe_int(usage.get("prompt_tokens") or usage.get("input_tokens"))
    output_tokens = _safe_int(usage.get("completion_tokens") or usage.get("output_tokens"))
    reasoning_tokens = _safe_int(usage.get("reasoning_tokens") or usage.get("reasoningTokens"))
    return OpenRouterUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        raw=usage,
    )


def _extract_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_text = item.get("text")
            if isinstance(item_text, str) and item_text.strip():
                chunks.append(item_text.strip())
        return "\n".join(chunks).strip()
    return ""


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.timeout_seconds = max(int(timeout_seconds), 5)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("openrouter_api_key_missing")
        url = f"{self.base_url}{path}"
        request = urllib.request.Request(
            url=url,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "HTTP-Referer": "https://cockpit.local",
                "X-Title": "Cockpit",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError("openrouter_invalid_json_object")
        return parsed

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        temperature: float = 0.2,
    ) -> OpenRouterChatResult:
        model_name = str(model or "").strip()
        if not model_name:
            return OpenRouterChatResult(
                status="failed",
                model="",
                text="",
                usage=OpenRouterUsage(0, 0, 0, {}),
                raw={},
                error="model_missing",
            )
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": bool(stream),
            "temperature": max(min(float(temperature), 2.0), 0.0),
        }
        try:
            response = self._post("/chat/completions", payload)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="ignore").strip()
            except Exception:
                detail = ""
            error = f"http_error:{exc.code}"
            if detail:
                error = f"{error}:{detail[:320]}"
            return OpenRouterChatResult(
                status="failed",
                model=model_name,
                text="",
                usage=OpenRouterUsage(0, 0, 0, {}),
                raw={},
                error=error,
            )
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            return OpenRouterChatResult(
                status="failed",
                model=model_name,
                text="",
                usage=OpenRouterUsage(0, 0, 0, {}),
                raw={},
                error=str(exc),
            )
        text = _extract_content(response)
        usage = _parse_usage(response)
        return OpenRouterChatResult(
            status="ok",
            model=model_name,
            text=text,
            usage=usage,
            raw=response,
            error=None,
        )

    def transcribe_audio(
        self,
        *,
        model: str,
        audio_base64: str,
        audio_format: str = "wav",
    ) -> OpenRouterChatResult:
        prompt = "Transcribe this audio exactly. Return plain text only."
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": str(audio_base64 or ""),
                            "format": str(audio_format or "wav"),
                        },
                    },
                ],
            }
        ]
        return self.chat(model=model, messages=messages, stream=False, temperature=0.0)

