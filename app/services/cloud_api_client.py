from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from threading import Lock
from typing import Any


API_BASE_URL_ENV = "COCKPIT_API_BASE_URL"
API_USERNAME_ENV = "COCKPIT_API_USERNAME"
API_PASSWORD_ENV = "COCKPIT_API_PASSWORD"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8100"

_ACCESS_TOKEN: str | None = None
_ACCESS_TOKEN_LOCK = Lock()


def _api_base_url() -> str:
    return str(os.environ.get(API_BASE_URL_ENV) or DEFAULT_API_BASE_URL).strip().rstrip("/")


def _credentials() -> tuple[str, str]:
    username = str(os.environ.get(API_USERNAME_ENV) or "").strip()
    password = str(os.environ.get(API_PASSWORD_ENV) or "").strip()
    if not username:
        raise RuntimeError(f"missing_env:{API_USERNAME_ENV}")
    if not password:
        raise RuntimeError(f"missing_env:{API_PASSWORD_ENV}")
    return username, password


def _request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any] | list[Any]:
    url = f"{_api_base_url()}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
        except Exception:
            detail = ""
        error = f"api_http_error:{exc.code}"
        if detail:
            error = f"{error}:{detail[:320]}"
        raise RuntimeError(error) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"api_unreachable:{exc}") from exc
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError("api_invalid_json_response") from exc
    if isinstance(parsed, (dict, list)):
        return parsed
    raise RuntimeError("api_invalid_response_type")


def _login() -> str:
    username, password = _credentials()
    payload = _request(
        "POST",
        "/v1/auth/login",
        payload={"username": username, "password": password},
        token=None,
    )
    if not isinstance(payload, dict):
        raise RuntimeError("api_login_invalid_payload")
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("api_login_missing_token")
    return token


def _auth_token(force_refresh: bool = False) -> str:
    global _ACCESS_TOKEN
    with _ACCESS_TOKEN_LOCK:
        if _ACCESS_TOKEN and not force_refresh:
            return _ACCESS_TOKEN
        _ACCESS_TOKEN = _login()
        return _ACCESS_TOKEN


def _authed_request(method: str, path: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    token = _auth_token(force_refresh=False)
    try:
        return _request(method, path, payload=payload, token=token)
    except RuntimeError as exc:
        if "api_http_error:401" not in str(exc):
            raise
    token = _auth_token(force_refresh=True)
    return _request(method, path, payload=payload, token=token)


def get_llm_profile(project_id: str) -> dict[str, Any]:
    payload = _authed_request("GET", f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/llm-profile")
    if not isinstance(payload, dict):
        raise RuntimeError("llm_profile_invalid_payload")
    profile = payload.get("profile")
    if not isinstance(profile, dict):
        raise RuntimeError("llm_profile_missing_profile")
    return profile


def put_llm_profile(project_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    payload = _authed_request("PUT", f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/llm-profile", payload=profile)
    if not isinstance(payload, dict):
        raise RuntimeError("llm_profile_put_invalid_payload")
    out = payload.get("profile")
    if not isinstance(out, dict):
        raise RuntimeError("llm_profile_put_missing_profile")
    return out


def post_agentic_turn(project_id: str, text: str, *, mode: str, thread_id: str | None = None) -> dict[str, Any]:
    payload = _authed_request(
        "POST",
        f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/chat/agentic-turn",
        payload={
            "text": text,
            "mode": mode,
            "thread_id": thread_id,
        },
    )
    if not isinstance(payload, dict):
        raise RuntimeError("agentic_turn_invalid_payload")
    return payload


def post_voice_transcribe(project_id: str, *, audio_base64: str, audio_format: str) -> dict[str, Any]:
    payload = _authed_request(
        "POST",
        f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/voice/transcribe",
        payload={
            "audio_base64": audio_base64,
            "format": audio_format,
        },
    )
    if not isinstance(payload, dict):
        raise RuntimeError("voice_transcribe_invalid_payload")
    return payload


def get_pixel_feed(project_id: str, window: str = "24h") -> dict[str, Any]:
    query = urllib.parse.urlencode({"window": window})
    payload = _authed_request("GET", f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/pixel-feed?{query}")
    if not isinstance(payload, dict):
        raise RuntimeError("pixel_feed_invalid_payload")
    return payload


def post_chat_message(project_id: str, text: str, *, thread_id: str | None = None) -> dict[str, Any]:
    payload = _authed_request(
        "POST",
        f"/v1/projects/{urllib.parse.quote(project_id, safe='')}/chat/messages",
        payload={"text": text, "thread_id": thread_id},
    )
    if not isinstance(payload, dict):
        raise RuntimeError("chat_post_invalid_payload")
    return payload
