from __future__ import annotations

import base64
import io
import json
import wave
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8787"
PROJECT_ID = "cockpit"


def _request(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        payload = json.loads(raw) if raw else {}
        return error.code, payload


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _silence_wav_base64() -> str:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 16000)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def main() -> int:
    status, payload = _request(
        f"/v1/projects/{PROJECT_ID}/voice/transcribe",
        method="POST",
        payload={"audio_base64": _silence_wav_base64(), "format": "wav"},
    )
    _assert(status == 200, f"voice transcribe returned {status}: {payload}")
    _assert(payload.get("project_id") == PROJECT_ID, f"unexpected voice payload: {payload}")
    _assert(isinstance(payload.get("status"), str), f"missing status: {payload}")
    _assert(isinstance(payload.get("model"), str), f"missing model: {payload}")
    _assert(isinstance(payload.get("duration_ms"), int), f"missing duration_ms: {payload}")
    _assert("text" in payload, f"missing text field: {payload}")
    if payload.get("status") == "failed":
        _assert(bool(payload.get("error")), f"failed transcription must include error: {payload}")

    print("OK: cockpit voice runtime verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
