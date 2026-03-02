from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


class TokenError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padded = raw + "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def hash_password(password: str, *, iterations: int = 250_000) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations_raw, salt, expected = str(encoded).split("$", 3)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    try:
        iterations = int(iterations_raw)
    except ValueError:
        return False
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(expected, computed)


def create_token(
    *,
    subject: str,
    role: str,
    permissions: list[str],
    secret_key: str,
    issuer: str,
    token_type: str,
    expires_seconds: int,
) -> str:
    now = _utc_now()
    payload = {
        "sub": subject,
        "role": role,
        "permissions": list(permissions),
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=max(int(expires_seconds), 60))).timestamp()),
        "typ": token_type,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_token(token: str, *, secret_key: str, issuer: str, expected_type: str | None = None) -> dict[str, Any]:
    raw = str(token or "").strip()
    parts = raw.split(".")
    if len(parts) != 3:
        raise TokenError("invalid token format")
    header_b64, payload_b64, signature_b64 = parts
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(signature_b64)
    except Exception as exc:
        raise TokenError(f"invalid signature encoding: {exc}") from exc
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise TokenError("invalid token signature")
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise TokenError(f"invalid payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise TokenError("invalid payload type")
    if str(payload.get("iss") or "") != issuer:
        raise TokenError("invalid issuer")
    token_type = str(payload.get("typ") or "")
    if expected_type and token_type != expected_type:
        raise TokenError(f"invalid token type: {token_type}")
    now_ts = int(_utc_now().timestamp())
    exp = int(payload.get("exp") or 0)
    if exp < now_ts:
        raise TokenError("token expired")
    return payload
