"""Testes da montagem e validação do snapshot de performance."""

from datetime import date, datetime, timezone

from flowscope.application.performance import (
    SCHEMA_VERSION_SNAPSHOT,
    SOURCE_GUI,
    PerformanceBenchmark,
    PerformanceTicker,
    chave_cache,
    montar_payload,
    montar_snapshot,
    snapshot_de_dict,
)

REF = date(2026, 11, 7)
CACHED_AT = datetime(2026, 11, 7, 18, 30, tzinfo=timezone.utc)
CLASSIFICACAO = {"PETR4": "ACAO", "HGLG11": "FII"}


def _benchmark(nome: str, disponivel: bool = True) -> PerformanceBenchmark:
    return PerformanceBenchmark(
        nome,
        (
            PerformanceTicker(
                ticker="HGLG11",
                ticker_return=0.12,
                index_return=0.05,
                excess_pp=7.0,
                observations=20,
                suspicious_event=True,
            ),
        ),
        disponivel,
        "total",
    )


def _payload() -> dict:
    return montar_payload(
        {"IFIX": _benchmark("IFIX")},
        CLASSIFICACAO,
        ["IFIX"],
        list(CLASSIFICACAO),
    )


class TestMontarPayload:
    def test_inclui_benchmarks_default_tipos_e_resultados(self):
        payload = _payload()
        assert payload["benchmarks"] == ["IFIX"]
        assert payload["default"] == "IBOV"
        assert payload["ticker_types"] == CLASSIFICACAO
        assert set(payload["results"]) == {"IFIX"}


class TestMontarSnapshot:
    def test_inclui_contexto_autodescritivo(self):
        snapshot = montar_snapshot(
            _payload(),
            ref_date=REF,
            period_days=30,
            sampling_method="fibonacci",
            source=SOURCE_GUI,
            cached_at=CACHED_AT,
        )
        assert snapshot["schema_version"] == SCHEMA_VERSION_SNAPSHOT
        assert snapshot["source"] == SOURCE_GUI
        assert snapshot["ref_date"] == "2026-11-07"
        assert snapshot["period_days"] == 30
        assert snapshot["sampling_method"] == "fibonacci"
        assert snapshot["cached_at"] == CACHED_AT.isoformat()
        assert snapshot["results"]["IFIX"]["return_basis"] == "total"

    def test_payload_sem_resultados(self):
        snapshot = montar_snapshot(
            montar_payload({}, {}, [], []),
            ref_date=REF,
            period_days=30,
            sampling_method="fibonacci",
            source=SOURCE_GUI,
            cached_at=CACHED_AT,
        )
        assert snapshot["benchmarks"] == []
        assert snapshot["results"] == {}
        assert snapshot["default"] is None


class TestSnapshotDeDict:
    def _valido(self) -> dict:
        return montar_snapshot(
            _payload(),
            ref_date=REF,
            period_days=30,
            sampling_method="fibonacci",
            source=SOURCE_GUI,
            cached_at=CACHED_AT,
        )

    def test_aceita_snapshot_valido(self):
        assert snapshot_de_dict(self._valido()) is not None

    def test_rejeita_nao_dicionario(self):
        assert snapshot_de_dict([]) is None
        assert snapshot_de_dict("x") is None

    def test_rejeita_schema_divergente(self):
        dados = self._valido()
        dados["schema_version"] = 99
        assert snapshot_de_dict(dados) is None

    def test_rejeita_resultados_nao_dicionario(self):
        dados = self._valido()
        dados["results"] = []
        assert snapshot_de_dict(dados) is None

    def test_rejeita_data_invalida(self):
        dados = self._valido()
        dados["ref_date"] = "amanha"
        assert snapshot_de_dict(dados) is None

    def test_rejeita_campos_de_contexto_ausentes(self):
        for campo in (
            "period_days",
            "sampling_method",
            "cached_at",
            "benchmarks",
            "ticker_types",
        ):
            dados = self._valido()
            dados.pop(campo)
            assert snapshot_de_dict(dados) is None


class TestChaveCache:
    def test_ordena_tickers_e_usa_a_base(self):
        chave = chave_cache(
            "IFIX", CLASSIFICACAO, REF, period_days=30, sampling_method="fibonacci"
        )
        assert chave.index == "IFIX"
        assert chave.tickers == ("HGLG11",)
        assert chave.return_basis == "total"

    def test_acao_usa_base_preco(self):
        chave = chave_cache(
            "IBOV", CLASSIFICACAO, REF, period_days=30, sampling_method="fibonacci"
        )
        assert chave.tickers == ("PETR4",)
        assert chave.return_basis == "price"
