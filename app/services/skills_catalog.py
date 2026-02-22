"""Skills Catalog Adapter — fetch, cache, and fail-open fallback.

ISSUE-CP-0001: Build reliable catalog fetch with local cache and
network fallback behavior.

Architecture:
  1. Try to fetch the curated catalog from the source.
  2. On success: return catalog + write to local cache.
  3. On failure (network down, timeout, parse error):
     - If local cache exists: return cached catalog + emit warning.
     - If no cache: return None + emit warning (caller handles fail-open).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogResult:
    """Result of a catalog fetch attempt."""
    catalog: list[dict[str, Any]] | None
    source: str  # "network" | "cache" | "unavailable"
    skill_count: int
    warnings: list[str] = field(default_factory=list)


# -- Default curated catalog (bundled) ------------------------------------
# This is the offline-safe baseline.  A real network fetch would replace
# this, but for now the curated list is embedded so the system always has
# a deterministic starting point.

DEFAULT_CURATED_CATALOG: list[dict[str, Any]] = [
    {"id": "openai-docs",     "name": "OpenAI Docs",     "version": "1.0", "curated": True},
    {"id": "skill-installer", "name": "Skill Installer",  "version": "1.0", "curated": True},
    {"id": "skill-creator",   "name": "Skill Creator",    "version": "1.0", "curated": True},
    {"id": "vercel-deploy",   "name": "Vercel Deploy",    "version": "1.0", "curated": True},
]


class SkillsCatalog:
    """Catalog adapter with cache and fail-open fallback.

    Usage::

        catalog = SkillsCatalog(projects_root / project_id)
        result = catalog.fetch()
        # result.catalog is the list of skills (or None if fully unavailable)
        # result.source tells you where it came from
    """

    CACHE_FILENAME = "catalog_cache.json"

    def __init__(self, project_path: Path) -> None:
        self._project_path = Path(project_path)
        self._cache_path = self._project_path / "skills" / self.CACHE_FILENAME

    # -- Public API -------------------------------------------------------

    def fetch(
        self,
        *,
        network_fetcher: Any | None = None,
    ) -> CatalogResult:
        """Fetch the curated catalog with cache fallback.

        Args:
            network_fetcher: Optional callable ``() -> list[dict]`` that
                fetches from a remote source.  If None, the default bundled
                catalog is used (safe offline mode).

        Returns:
            A :class:`CatalogResult` with the catalog payload and metadata.
        """
        # 1) Try network/source fetch
        fetched_catalog = self._try_fetch(network_fetcher)

        if fetched_catalog is not None:
            self._write_cache(fetched_catalog)
            return CatalogResult(
                catalog=fetched_catalog,
                source="network",
                skill_count=len(fetched_catalog),
            )

        # 2) Fallback to cache
        cached = self._read_cache()
        if cached is not None:
            warning = "Network fetch failed — using cached catalog."
            logger.warning(warning)
            return CatalogResult(
                catalog=cached,
                source="cache",
                skill_count=len(cached),
                warnings=[warning],
            )

        # 3) Fully unavailable
        warning = "Catalog unavailable — no network, no cache."
        logger.warning(warning)
        return CatalogResult(
            catalog=None,
            source="unavailable",
            skill_count=0,
            warnings=[warning],
        )

    @property
    def cache_path(self) -> Path:
        """Path to the local cache file."""
        return self._cache_path

    def clear_cache(self) -> bool:
        """Remove the local cache file.  Returns True if a file was removed."""
        if self._cache_path.exists():
            self._cache_path.unlink()
            return True
        return False

    # -- Internals --------------------------------------------------------

    def _try_fetch(self, fetcher: Any | None) -> list[dict[str, Any]] | None:
        """Attempt to get catalog from source.  Returns None on failure."""
        try:
            if fetcher is not None:
                result = fetcher()
                if isinstance(result, list):
                    return result
                return None
            # Default: return the bundled curated catalog
            return list(DEFAULT_CURATED_CATALOG)
        except Exception as exc:
            logger.warning("Catalog fetch failed: %s", exc)
            return None

    def _read_cache(self) -> list[dict[str, Any]] | None:
        """Read catalog from local cache.  Returns None if missing or corrupt."""
        if not self._cache_path.exists():
            return None
        try:
            with self._cache_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
            # Handle wrapped format: {"catalog": [...], "cached_at": "..."}
            if isinstance(data, dict) and isinstance(data.get("catalog"), list):
                return data["catalog"]
            return None
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache read failed: %s", exc)
            return None

    def _write_cache(self, catalog: list[dict[str, Any]]) -> None:
        """Write catalog to local cache (atomic-safe)."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "skill_count": len(catalog),
                "catalog": catalog,
            }
            tmp = self._cache_path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            tmp.replace(self._cache_path)
        except OSError as exc:
            logger.warning("Cache write failed: %s", exc)
