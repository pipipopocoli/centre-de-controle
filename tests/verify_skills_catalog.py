"""Verify Skills Catalog Adapter (ISSUE-CP-0001).

Covers: default fetch, cache write, cache fallback, no-cache-no-network,
custom fetcher, fetcher failure, corrupt cache, and deterministic output.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.skills_catalog import CatalogResult, SkillsCatalog  # noqa: E402


def test_default_fetch_returns_bundled() -> None:
    """Default fetch (no network fetcher) returns the bundled curated catalog."""
    with tempfile.TemporaryDirectory() as tmp:
        catalog = SkillsCatalog(Path(tmp))
        result = catalog.fetch()
        assert result.source == "network"
        assert result.catalog is not None
        assert result.skill_count >= 4
        assert len(result.warnings) == 0
    print("[PASS] default fetch returns bundled catalog")


def test_cache_written_after_fetch() -> None:
    """After a successful fetch, the cache file must exist."""
    with tempfile.TemporaryDirectory() as tmp:
        catalog = SkillsCatalog(Path(tmp))
        catalog.fetch()
        assert catalog.cache_path.exists()
        data = json.loads(catalog.cache_path.read_text())
        assert "catalog" in data
        assert "cached_at" in data
        assert data["skill_count"] >= 4
    print("[PASS] cache written after fetch")


def test_cache_fallback_when_network_fails() -> None:
    """When network fails but cache exists, catalog comes from cache."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        # Seed the cache with a normal fetch
        cat.fetch()
        assert cat.cache_path.exists()

        # Now fetch with a broken network fetcher
        def broken_fetcher():
            raise ConnectionError("no network")

        result = cat.fetch(network_fetcher=broken_fetcher)
        assert result.source == "cache"
        assert result.catalog is not None
        assert result.skill_count >= 4
        assert len(result.warnings) == 1
        assert "cached" in result.warnings[0].lower()
    print("[PASS] cache fallback when network fails")


def test_unavailable_no_cache_no_network() -> None:
    """When network fails and no cache exists, catalog is None."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))

        def broken_fetcher():
            raise ConnectionError("no network")

        result = cat.fetch(network_fetcher=broken_fetcher)
        assert result.source == "unavailable"
        assert result.catalog is None
        assert result.skill_count == 0
        assert len(result.warnings) == 1
    print("[PASS] unavailable when no cache and no network")


def test_custom_fetcher_success() -> None:
    """A custom fetcher returning a list is used as-is."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        custom = [{"id": "custom-skill", "version": "2.0"}]

        result = cat.fetch(network_fetcher=lambda: custom)
        assert result.source == "network"
        assert result.skill_count == 1
        assert result.catalog[0]["id"] == "custom-skill"
    print("[PASS] custom fetcher success")


def test_fetcher_returning_non_list() -> None:
    """A fetcher returning a non-list triggers fallback."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        result = cat.fetch(network_fetcher=lambda: "not a list")
        # No cache exists, so should be unavailable
        assert result.source == "unavailable"
        assert result.catalog is None
    print("[PASS] fetcher returning non-list triggers fallback")


def test_corrupt_cache_ignored() -> None:
    """A corrupt cache file is ignored gracefully."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        # Write garbage to cache
        cat.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cat.cache_path.write_text("{invalid json!!!")

        def broken_fetcher():
            raise ConnectionError("no net")

        result = cat.fetch(network_fetcher=broken_fetcher)
        assert result.source == "unavailable"
        assert result.catalog is None
    print("[PASS] corrupt cache ignored gracefully")


def test_deterministic_output() -> None:
    """Two successive fetches return the same catalog content."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        r1 = cat.fetch()
        r2 = cat.fetch()
        assert r1.catalog == r2.catalog
        assert r1.skill_count == r2.skill_count
    print("[PASS] deterministic output")


def test_clear_cache() -> None:
    """clear_cache removes the file and returns True; second call returns False."""
    with tempfile.TemporaryDirectory() as tmp:
        cat = SkillsCatalog(Path(tmp))
        cat.fetch()
        assert cat.cache_path.exists()
        assert cat.clear_cache() is True
        assert not cat.cache_path.exists()
        assert cat.clear_cache() is False
    print("[PASS] clear_cache")


def main() -> int:
    tests = [
        test_default_fetch_returns_bundled,
        test_cache_written_after_fetch,
        test_cache_fallback_when_network_fails,
        test_unavailable_no_cache_no_network,
        test_custom_fetcher_success,
        test_fetcher_returning_non_list,
        test_corrupt_cache_ignored,
        test_deterministic_output,
        test_clear_cache,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: skills catalog verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
