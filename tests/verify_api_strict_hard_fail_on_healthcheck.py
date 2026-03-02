#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import _check_api_health  # noqa: E402


class _FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    def read(self) -> bytes:
        return self._body.encode("utf-8")

    def getcode(self) -> int:
        return self.status


def main() -> int:
    with patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
        ok, detail = _check_api_health("http://127.0.0.1:8100", 0.25)
        assert ok is False
        assert "unreachable" in detail

    with patch("urllib.request.urlopen", return_value=_FakeResponse(200, '{"status":"ok"}')):
        ok, detail = _check_api_health("http://127.0.0.1:8100", 0.25)
        assert ok is True
        assert detail == "ok"

    with patch("urllib.request.urlopen", return_value=_FakeResponse(503, '{"status":"down"}')):
        ok, detail = _check_api_health("http://127.0.0.1:8100", 0.25)
        assert ok is False
        assert "status 503" in detail

    with patch("urllib.request.urlopen", return_value=_FakeResponse(200, io.StringIO("bad").getvalue())):
        ok, detail = _check_api_health("http://127.0.0.1:8100", 0.25)
        assert ok is False
        assert "unexpected payload" in detail

    print("OK: api strict healthcheck hard-fail contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
