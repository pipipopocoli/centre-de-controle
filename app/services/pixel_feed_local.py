from __future__ import annotations

from app.data.paths import project_dir


def _empty_feed(project_id: str, window: str) -> dict:
    return {
        "project_id": project_id,
        "window": window,
        "bucket_minutes": 60,
        "generated_at_utc": "",
        "rows": [],
    }


def build_local_pixel_feed(project_id: str, *, window: str = "24h") -> dict:
    path = project_dir(project_id)
    if not path.exists():
        return _empty_feed(project_id, window)
    try:
        # Lazy import to avoid triggering server/__init__.py at module load.
        import importlib
        mod = importlib.import_module("server.analytics.pixel_feed")
        return mod.build_pixel_feed(project_dir=path, project_id=project_id, window=window)
    except Exception:
        return _empty_feed(project_id, window)


