from __future__ import annotations

import importlib
import importlib.metadata
import platform
import sys


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _check_import(name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(name)
        version = _package_version(name)
        return True, version or "unknown"
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, str(exc)


def main() -> int:
    print("Centre de controle - Setup Doctor")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")

    ok = True
    for module in ("PySide6", "mcp"):
        success, detail = _check_import(module)
        status = "OK" if success else "MISSING"
        print(f"{module}: {status} ({detail})")
        ok = ok and success

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
