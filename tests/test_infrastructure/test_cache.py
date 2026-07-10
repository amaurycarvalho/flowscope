import json
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.cache import CacheManager


@pytest.fixture
def cache(tmp_path: Path) -> CacheManager:
    return CacheManager(cache_dir=tmp_path)


def _write_meta(tmp_path: Path, key: str, payload: dict) -> Path:
    meta = tmp_path / f"{key}.json"
    meta.write_text(json.dumps(payload, default=str), encoding="utf-8")
    return meta


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


class TestGetOrFetch:
    def test_cache_valido_retorna_dado_sem_executar_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        payload = {"cached_at": datetime.now().isoformat(), "data": "cached"}
        _write_meta(cache._cache_dir, "mykey", payload)
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result == payload
        fetch_fn.assert_not_called()

    def test_cache_expirado_executa_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        old = (datetime.now() - timedelta(days=10)).isoformat()
        payload = {"cached_at": old, "data": "stale"}
        _write_meta(cache._cache_dir, "mykey", payload)
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result["data"] == "fresh"
        fetch_fn.assert_called_once()

    def test_cache_ausente_executa_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result["data"] == "fresh"
        fetch_fn.assert_called_once()

    def test_meta_corrompida_executa_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        (cache._cache_dir / "mykey.json").write_text("not-json", encoding="utf-8")
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result["data"] == "fresh"


class TestInvalidate:
    def test_chave_existente_remove_arquivo(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "x"})
        cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        meta_path = cache._cache_dir / "mykey.json"
        assert meta_path.exists()
        cache.invalidate("mykey")
        assert not meta_path.exists()

    def test_chave_inexistente_nao_levanta_excecao(self, cache: CacheManager):
        cache.invalidate("ghost")


class TestFindNearest:
    def test_exact_date_found(self, cache: CacheManager):
        d = date(2026, 7, 10)
        cache.put(d, "data")
        result = cache.find_nearest(d)
        assert result == d

    def test_within_deviation(self, cache: CacheManager):
        cache.put(date(2026, 7, 10), "data")
        result = cache.find_nearest(date(2026, 7, 12), max_deviation=3)
        assert result == date(2026, 7, 10)

    def test_empty_cache(self, cache: CacheManager):
        result = cache.find_nearest(date(2026, 7, 10))
        assert result is None

    def test_beyond_deviation(self, cache: CacheManager):
        cache.put(date(2026, 7, 10), "data")
        result = cache.find_nearest(date(2026, 7, 20), max_deviation=3)
        assert result is None

    def test_prefers_closer_date(self, cache: CacheManager):
        cache.put(date(2026, 7, 10), "data")
        cache.put(date(2026, 7, 15), "data")
        result = cache.find_nearest(date(2026, 7, 12), max_deviation=5)
        assert result == date(2026, 7, 10)

    def test_zero_deviation(self, cache: CacheManager):
        cache.put(date(2026, 7, 10), "data")
        result = cache.find_nearest(date(2026, 7, 10), max_deviation=0)
        assert result == date(2026, 7, 10)
