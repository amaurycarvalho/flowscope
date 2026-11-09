import json
import logging
from datetime import date
from unittest.mock import MagicMock

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.performance import (
    PerformanceBenchmark,
    PerformanceTicker,
)
from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.background.events import Resultado
from flowscope.infrastructure.performance import JsonPerformanceSnapshotStore
from flowscope.presentation.gui.controller_performance import (
    PerformanceMixin,
    executar_performance,
)

REF = date(2026, 1, 9)
CONFIG = SamplingConfig(period_days=30, method="fibonacci")
CLASSIFICACAO = {"PETR4": "ACAO", "HGLG11": "FII"}
CURRENT = {"PETR4": {"daily_data": []}, "HGLG11": {"daily_data": []}}


class FakeCache:
    def __init__(self):
        self.store = {}
        self.registros = 0

    def obter(self, chave):
        return self.store.get(chave.identidade())

    def registrar(self, chave, resultado):
        self.store[chave.identidade()] = resultado
        self.registros += 1


class FakeCase:
    def __init__(self):
        self.calls = []

    def execute(self, current, classificacao, ref_date, benchmarks=None):
        self.calls.append((current, classificacao, ref_date, benchmarks))
        return {b: _benchmark(b) for b in benchmarks or []}


class FakeCtx:
    def __init__(self):
        self.valor = None

    def raise_if_cancelled(self):
        pass

    def resultado(self, valor=None, **kwargs):
        self.valor = valor


def _benchmark(nome: str) -> PerformanceBenchmark:
    return PerformanceBenchmark(
        nome,
        (
            PerformanceTicker(
                ticker="PETR4",
                ticker_return=0.1,
                index_return=0.05,
                excess_pp=5.0,
                observations=2,
            ),
        ),
        True,
        "price",
    )


class TestExecutarPerformance:
    def test_calcula_e_grava_no_cache(self):
        cache = FakeCache()
        caso = FakeCase()
        ctx = FakeCtx()
        executar_performance(
            ctx, caso, cache, CURRENT, CLASSIFICACAO, list(CLASSIFICACAO),
            REF, CONFIG,
        )
        assert ctx.valor["benchmarks"] == ["IFIX", "IBOV", "IDIV"]
        assert ctx.valor["default"] == "IBOV"
        assert set(ctx.valor["results"]) == {"IFIX", "IBOV", "IDIV"}
        assert cache.registros == 3
        assert caso.calls[0][3] == ["IFIX", "IBOV", "IDIV"]

    def test_reutiliza_cache_sem_recalcular(self):
        cache = FakeCache()
        caso = FakeCase()
        executar_performance(
            FakeCtx(), caso, cache, CURRENT, CLASSIFICACAO,
            list(CLASSIFICACAO), REF, CONFIG,
        )
        ctx = FakeCtx()
        executar_performance(
            ctx, caso, cache, CURRENT, CLASSIFICACAO,
            list(CLASSIFICACAO), REF, CONFIG,
        )
        assert len(caso.calls) == 1
        assert cache.registros == 3
        assert set(ctx.valor["results"]) == {"IFIX", "IBOV", "IDIV"}

    def test_sem_benchmarks_elegiveis(self):
        ctx = FakeCtx()
        executar_performance(
            ctx, FakeCase(), FakeCache(), {}, {}, [], REF, CONFIG
        )
        assert ctx.valor == {
            "benchmarks": [], "default": None, "ticker_types": {}, "results": {},
        }

    def test_registra_ciclo_no_log(self, caplog):
        with caplog.at_level(logging.INFO, logger="flowscope"):
            executar_performance(
                FakeCtx(), FakeCase(), FakeCache(), CURRENT, CLASSIFICACAO,
                list(CLASSIFICACAO), REF, CONFIG,
            )
        assert "Performance: início do processamento" in caplog.text
        assert "Performance: processamento concluído" in caplog.text

    def test_cancelamento_nao_propaga_resultado(self):
        class _CtxCancelado(FakeCtx):
            def raise_if_cancelled(self):
                raise OperacaoCancelada()

        ctx = _CtxCancelado()
        executar_performance(
            ctx, FakeCase(), FakeCache(), CURRENT, CLASSIFICACAO,
            list(CLASSIFICACAO), REF, CONFIG,
        )
        assert ctx.valor is None


class _PresenterFake:
    def __init__(self, gui):
        self._gui = gui

    def get_sampling_config(self):
        return CONFIG

    def on_performance_result(self, dados):
        self._gui.set_performance_data(dados)


class _GuiFake:
    def __init__(self):
        self._fundamental_data = {"PETR4": {
            "classificacao": {"tipo": "acao"},
        }}
        self._current_data = CURRENT
        self.performance = None

    def set_performance_data(self, dados):
        self.performance = dados


class _BackgroundFake:
    def __init__(self):
        self.submetido = None

    def submit(self, trabalho, **kwargs):
        self.submetido = (trabalho, kwargs)


class _Controller(PerformanceMixin):
    def __init__(self, background):
        self._performance_use_case = FakeCase()
        self._performance_cache = FakeCache()
        self._background = background
        self._presenter = _PresenterFake(_GuiFake())
        self._fundamental_resolver_fiagro = None


class TestSnapshotGui:
    def test_grava_latest_json_com_contexto_da_carga(self, tmp_path):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        executar_performance(
            FakeCtx(), FakeCase(), FakeCache(), CURRENT, CLASSIFICACAO,
            list(CLASSIFICACAO), REF, CONFIG, snapshot_store=store,
        )
        snapshot = json.loads(store.caminho.read_text(encoding="utf-8"))
        assert snapshot["source"] == "gui"
        assert snapshot["ref_date"] == REF.isoformat()
        assert snapshot["period_days"] == CONFIG.period_days
        assert snapshot["sampling_method"] == CONFIG.method
        assert set(snapshot["results"]) == {"IFIX", "IBOV", "IDIV"}

    def test_sem_benchmarks_ainda_grava_contexto(self, tmp_path):
        store = JsonPerformanceSnapshotStore(cache_dir=tmp_path)
        executar_performance(
            FakeCtx(), FakeCase(), FakeCache(), {}, {}, [], REF, CONFIG,
            snapshot_store=store,
        )
        snapshot = json.loads(store.caminho.read_text(encoding="utf-8"))
        assert snapshot["results"] == {}
        assert snapshot["ref_date"] == REF.isoformat()


class TestPerformanceMixin:
    def test_dispara_apos_carga(self):
        background = _BackgroundFake()
        controller = _Controller(background)
        controller._iniciar_analise_performance(list(CURRENT), REF, CURRENT)
        assert background.submetido is not None
        trabalho, kwargs = background.submetido
        assert kwargs["grupo"] == "performance"
        ctx = FakeCtx()
        trabalho(ctx)
        kwargs["ao_resultado"](Resultado(valor=ctx.valor))
        assert controller._presenter._gui.performance is not None

    def test_sem_dependencias_nao_dispara(self):
        background = _BackgroundFake()
        controller = _Controller(background)
        controller._performance_use_case = None
        controller._iniciar_analise_performance(list(CURRENT), REF, CURRENT)
        assert background.submetido is None

    def test_resultado_grava_performance_sem_tocar_current_data(self):
        background = _BackgroundFake()
        controller = _Controller(background)
        atual = dict(controller._presenter._gui._current_data)
        controller._ao_resultado_performance(
            Resultado(valor={"benchmarks": ["IBOV"]})
        )
        assert controller._presenter._gui.performance == {"benchmarks": ["IBOV"]}
        assert controller._presenter._gui._current_data == atual
