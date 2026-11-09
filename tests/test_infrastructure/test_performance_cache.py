import json
from datetime import date
from unittest.mock import patch

from flowscope.application.performance.modelos import PerformanceCacheKey
from flowscope.infrastructure.performance import JsonPerformanceCache


def _chave(**mudancas) -> PerformanceCacheKey:
    valores = {
        "schema_version": 1,
        "index": "IBOV",
        "ref_date": date(2026, 1, 9),
        "period_days": 30,
        "sampling_method": "fibonacci",
        "tickers": ("PETR4", "VALE3"),
        "return_basis": "price",
    }
    valores.update(mudancas)
    return PerformanceCacheKey(**valores)


class TestJsonPerformanceCache:
    def test_reutiliza_mesma_chave(self, tmp_path):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        cache.registrar(_chave(), {"benchmark": "IBOV"})
        assert cache.obter(_chave()) == {"benchmark": "IBOV"}

    def test_chave_ausente(self, tmp_path):
        assert JsonPerformanceCache(cache_dir=tmp_path).obter(_chave()) is None

    def test_mudanca_de_parametro_invalida(self, tmp_path):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        cache.registrar(_chave(), {"benchmark": "IBOV"})
        assert cache.obter(_chave(period_days=60)) is None
        assert cache.obter(_chave(tickers=("PETR4",))) is None
        assert cache.obter(_chave(index="IFIX")) is None

    def test_mudanca_de_schema_invalida(self, tmp_path):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        cache.registrar(_chave(), {"benchmark": "IBOV"})
        assert cache.obter(_chave(schema_version=2)) is None

    def test_corrupcao_retorna_ausencia(self, tmp_path):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        caminho = cache._path_for(_chave())
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("not-json", encoding="utf-8")
        assert cache.obter(_chave()) is None

    def test_schema_armazenado_divergente(self, tmp_path):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        caminho = cache._path_for(_chave())
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(
            json.dumps({"schema_version": 99, "resultado": {"x": 1}}),
            encoding="utf-8",
        )
        assert cache.obter(_chave()) is None

    def test_falha_de_escrita_nao_propaga(self, tmp_path, caplog):
        cache = JsonPerformanceCache(cache_dir=tmp_path)
        with patch(
            "flowscope.infrastructure.performance.cache._atomic_write_bytes",
            side_effect=OSError("sem espaço"),
        ):
            cache.registrar(_chave(), {"benchmark": "IBOV"})
        assert "Falha ao gravar o cache de performance" in caplog.text
