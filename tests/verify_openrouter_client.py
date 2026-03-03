from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.llm.openrouter_client import OpenRouterClient  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def main() -> int:
    captured: dict[str, object] = {}

    def _fake_urlopen(request, timeout=0):  # noqa: ANN001
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(
            {
                "choices": [{"message": {"content": "hello cockpit"}}],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 7,
                    "reasoningTokens": 3,
                },
            }
        )

    client = OpenRouterClient(api_key="test-key", base_url="https://openrouter.ai/api/v1", timeout_seconds=33)
    with patch("server.llm.openrouter_client.urllib.request.urlopen", side_effect=_fake_urlopen):
        chat = client.chat(model="arcee-ai/trinity-large-preview:free", messages=[{"role": "user", "content": "hi"}])
        assert chat.status == "ok"
        assert chat.text == "hello cockpit"
        assert chat.usage.input_tokens == 12
        assert chat.usage.output_tokens == 7
        assert chat.usage.reasoning_tokens == 3

        transcribe = client.transcribe_audio(
            model="google/gemini-2.5-flash",
            audio_base64="UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB",
            audio_format="wav",
        )
        assert transcribe.status == "ok"

    payload = captured.get("payload")
    assert isinstance(payload, dict)
    assert payload.get("model"), payload
    print("OK: openrouter client verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

