import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flowscope.infrastructure.cache import CacheManager


@pytest.fixture
def cache(tmp_path: Path) -> CacheManager:
    return CacheManager(cache_dir=tmp_path)


def _write_meta(tmp_path: Path, key: str, payload: dict) -> Path:
    meta = tmp_path / f"{key}.json"
    meta.write_text(json.dumps(payload, default=str), encoding="utf-8")
    return meta


class TestPathFor:
    def test_path_for_formats_date(self, cache: CacheManager):
        path = cache._path_for(date(2026, 6, 25))
        assert path == cache._cache_dir / "2026-06-25.csv"
        assert path.name == "2026-06-25.csv"


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

    def test_get_reads_with_utf8(self, cache: CacheManager):
        path = MagicMock()
        path.exists.return_value = True
        path.read_text.return_value = "data"
        with patch.object(cache, "_path_for", return_value=path):
            result = cache.get(date(2026, 6, 25))
        assert result == "data"
        path.read_text.assert_called_once_with(encoding="utf-8")

    def test_overwrite(self, cache: CacheManager):
        d = date(2026, 6, 25)
        cache.put(d, "first")
        cache.put(d, "second")
        assert cache.get(d) == "second"

    def test_get_cache_dir(self, cache: CacheManager, tmp_path: Path):
        assert cache.get_cache_dir() == tmp_path

    def test_put_mkdir_with_parents(self, cache: CacheManager):
        with patch.object(Path, "mkdir") as mock_mkdir:
            cache.put(date(2026, 6, 25), "data")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_put_writes_tmp_with_utf8_then_renames(self, cache: CacheManager):
        path = MagicMock()
        tmp = path.with_suffix.return_value
        with patch.object(cache, "_path_for", return_value=path):
            cache.put(date(2026, 6, 25), "data")
        path.with_suffix.assert_called_once_with(".tmp")
        tmp.write_text.assert_called_once_with("data", encoding="utf-8")
        tmp.rename.assert_called_once_with(path)


class TestGetOrFetch:
    def test_cache_valido_retorna_dado_sem_executar_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        payload = {"cached_at": datetime.now(timezone.utc).isoformat(), "data": "cached"}
        _write_meta(cache._cache_dir, "mykey", payload)
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result == payload
        fetch_fn.assert_not_called()

    def test_cache_naive_timestamp_normalized(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        payload = {"cached_at": datetime.now().isoformat(), "data": "cached"}
        _write_meta(cache._cache_dir, "mykey", payload)
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result == payload
        fetch_fn.assert_not_called()

    def test_cache_expira_na_fronteira_do_ttl(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        old = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        _write_meta(cache._cache_dir, "mykey", {"cached_at": old, "data": "stale"})
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result["data"] == "fresh"
        fetch_fn.assert_called_once()

    def test_get_or_fetch_reads_meta_with_utf8(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        meta_path = MagicMock()
        meta_path.exists.return_value = True
        payload = {"cached_at": datetime.now(timezone.utc).isoformat(), "data": "cached"}
        meta_path.read_text.return_value = json.dumps(payload)
        with patch.object(cache, "_meta_path_for", return_value=meta_path):
            result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result == payload
        fetch_fn.assert_not_called()
        meta_path.read_text.assert_called_once_with(encoding="utf-8")

    def test_cache_expirado_executa_fetch(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
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

    def test_get_or_fetch_mkdir_with_parents(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        with patch.object(Path, "mkdir") as mock_mkdir:
            cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_or_fetch_payload_has_cached_at_key(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert "cached_at" in result
        assert result["data"] == "fresh"

    def test_get_or_fetch_uses_utc_timestamp(self, cache: CacheManager):
        fetch_fn = MagicMock(return_value={"data": "fresh"})
        result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        assert result["cached_at"].endswith("+00:00")

    def test_get_or_fetch_writes_tmp_then_renames(self, cache: CacheManager):
        import json as json_module

        fetch_fn = MagicMock(return_value={"data": "fresh"})
        meta_path = MagicMock()
        meta_path.exists.return_value = False
        with patch.object(cache, "_meta_path_for", return_value=meta_path):
            with patch(
                "flowscope.infrastructure.cache.json.dumps",
                wraps=json_module.dumps,
            ) as mock_dumps:
                result = cache.get_or_fetch("mykey", ttl_days=7, fetch_fn=fetch_fn)
        meta_path.with_suffix.assert_called_once_with(".tmp")
        tmp = meta_path.with_suffix.return_value
        tmp.write_text.assert_called_once()
        assert tmp.write_text.call_args.kwargs["encoding"] == "utf-8"
        tmp.rename.assert_called_once_with(meta_path)
        mock_dumps.assert_called_once()
        dump_args, dump_kwargs = mock_dumps.call_args
        assert dump_args[0]["data"] == "fresh"
        assert "cached_at" in dump_args[0]
        assert dump_kwargs["indent"] == 2
        assert dump_kwargs["default"] == str
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

    def test_finds_future_date(self, cache: CacheManager):
        cache.put(date(2026, 7, 12), "data")
        result = cache.find_nearest(date(2026, 7, 10), max_deviation=3)
        assert result == date(2026, 7, 12)

    def test_empty_cache(self, cache: CacheManager):
        result = cache.find_nearest(date(2026, 7, 10))
        assert result is None

    def test_beyond_deviation(self, cache: CacheManager):
        cache.put(date(2026, 7, 10), "data")
        result = cache.find_nearest(date(2026, 7, 20), max_deviation=3)
        assert result is None

    def test_default_deviation_is_seven(self, cache: CacheManager):
        cache.put(date(2026, 7, 2), "data")
        result = cache.find_nearest(date(2026, 7, 10))
        assert result is None

    def test_one_day_deviation_ignores_two_days(self, cache: CacheManager):
        cache.put(date(2026, 7, 8), "data")
        result = cache.find_nearest(date(2026, 7, 10), max_deviation=1)
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

