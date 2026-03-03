from __future__ import annotations

from app.data.paths import project_dir
from server.analytics.pixel_feed import build_pixel_feed


def build_local_pixel_feed(project_id: str, *, window: str = "24h") -> dict:
    path = project_dir(project_id)
    return build_pixel_feed(project_dir=path, project_id=project_id, window=window)

