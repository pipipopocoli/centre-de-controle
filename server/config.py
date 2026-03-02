from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


@dataclass(frozen=True)
class APISettings:
    projects_root: Path
    secret_key: str
    issuer: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int

    @classmethod
    def from_env(cls) -> "APISettings":
        projects_root_raw = os.environ.get("COCKPIT_API_PROJECTS_ROOT") or str(_default_projects_root())
        secret_key = os.environ.get("COCKPIT_API_SECRET") or "cockpit-dev-secret-change-me"
        issuer = os.environ.get("COCKPIT_API_ISSUER") or "cockpit-api"
        access_ttl = int(os.environ.get("COCKPIT_API_ACCESS_TTL_SECONDS") or "3600")
        refresh_ttl = int(os.environ.get("COCKPIT_API_REFRESH_TTL_SECONDS") or str(60 * 60 * 24 * 7))
        return cls(
            projects_root=Path(projects_root_raw).expanduser(),
            secret_key=secret_key,
            issuer=issuer,
            access_ttl_seconds=max(access_ttl, 60),
            refresh_ttl_seconds=max(refresh_ttl, 300),
        )
