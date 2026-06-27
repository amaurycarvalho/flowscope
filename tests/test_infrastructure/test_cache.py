from datetime import date
from pathlib import Path

import pytest

from flowscope.infrastructure.cache import CacheManager


@pytest.fixture
def cache(tmp_path: Path) -> CacheManager:
    return CacheManager(cache_dir=tmp_path)


class TestCacheManager:
    def test_put_and_get(self, cache: CacheManager):
        d = date(2026, 6, 25)
        content = "test,csv,data"
        cache.put(d, content)
        retrieved = cache.get(d)
        assert retrieved == content

    def test_get_missing(self, cache: CacheManager):
        d = date(2026, 6, 26)
        assert cache.get(d) is None

    def test_overwrite(self, cache: CacheManager):
        d = date(2026, 6, 25)
        cache.put(d, "first")
        cache.put(d, "second")
        assert cache.get(d) == "second"

    def test_get_cache_dir(self, cache: CacheManager, tmp_path: Path):
        assert cache.get_cache_dir() == tmp_path
