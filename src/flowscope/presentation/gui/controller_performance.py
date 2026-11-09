"""Job de performance versus índice disparado após a carga principal.

A classificação FII × Ação é capturada na thread do Tk (a partir de
``_fundamental_data``) e o cálculo roda em background. O resultado é gravado
em ``_performance_data`` pela view, sem tocar em ``_current_data``.
"""

import logging
from collections.abc import Mapping, Sequence
from datetime import date

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.performance import (
    SOURCE_GUI,
    AnalyzePerformanceUseCase,
    PerformanceCache,
    benchmarks_disponiveis,
    classificar_elegiveis,
    gravar_cache,
    ler_cache,
    montar_payload,
    montar_snapshot,
)
from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Resultado
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

#: Grupo e política do job de performance no gerenciador de background.
GRUPO_PERFORMANCE = "performance"
POLITICA_PERFORMANCE = Politica.LATEST_WINS


class PerformanceMixin:
    """Mixin que dispara o cálculo de performance em background."""

    def _iniciar_analise_performance(
        self: "PerformanceMixin",
        tickers: list[str],
        ref_date: date,
        result: dict | None = None,
    ) -> None:
        """Dispara o job de performance, se o caso de uso estiver configurado."""
        caso = getattr(self, "_performance_use_case", None)
        cache = getattr(self, "_performance_cache", None)
        snapshot_store = getattr(self, "_performance_snapshot_store", None)
        if caso is None or cache is None or self._background is None:
            logger.debug(
                "Performance não iniciada: caso de uso, cache ou background ausente"
            )
            return
        gui = self._presenter._gui
        fundamental = getattr(gui, "_fundamental_data", {}) or {}
        classificacao = classificar_elegiveis(
            tickers,
            fundamental,
            getattr(self, "_fundamental_resolver_fiagro", None),
        )
        excluidos = [ticker for ticker in tickers if ticker not in classificacao]
        if excluidos:
            logger.info(
                "Performance: tickers fora por tipo não elegível: %s", excluidos
            )
        current = result or getattr(gui, "_current_data", {}) or {}
        config = self._presenter.get_sampling_config()
        logger.info(
            "Performance: agendando cálculo (%d tickers, benchmarks=%s, data=%s)",
            len(tickers),
            benchmarks_disponiveis(classificacao),
            ref_date,
        )
        self._background.submit(
            lambda ctx: executar_performance(
                ctx, caso, cache, current, classificacao, list(tickers),
                ref_date, config, snapshot_store=snapshot_store,
            ),
            grupo=GRUPO_PERFORMANCE,
            politica=POLITICA_PERFORMANCE,
            cancelavel=True,
            ao_resultado=self._ao_resultado_performance,
            ao_erro=self._ao_erro_performance,
        )

    def _ao_resultado_performance(
        self: "PerformanceMixin", evento: Resultado
    ) -> None:
        """Aplica o resultado do job na view, sem tocar nos dados da carga."""
        self._presenter.on_performance_result(evento.valor)

    def _ao_erro_performance(self: "PerformanceMixin", evento: Erro) -> None:
        """Registra a falha do job auxiliar sem interromper a interface."""
        logger.warning(
            "Falha no cálculo de performance: %s", evento.excecao
        )


def executar_performance(
    ctx: JobContext,
    caso: AnalyzePerformanceUseCase,
    cache: PerformanceCache,
    current_data: Mapping[str, object],
    classificacao: Mapping[str, str],
    tickers: Sequence[str],
    ref_date: date,
    config: SamplingConfig,
    snapshot_store: object | None = None,
) -> None:
    """Calcula (ou reutiliza do cache) cada benchmark e publica o payload."""
    benchmarks = benchmarks_disponiveis(classificacao)
    logger.info(
        "Performance: início do processamento (%d tickers, benchmarks=%s)",
        len(tickers),
        benchmarks,
    )
    if not benchmarks:
        logger.info("Performance: nenhum benchmark elegível para a seleção")
        payload = montar_payload({}, classificacao, benchmarks, tickers)
        _gravar_snapshot(payload, ref_date, config, snapshot_store)
        ctx.resultado(valor=payload)
        return
    try:
        payload = _processar(
            ctx, caso, cache, current_data, classificacao, tickers,
            ref_date, config, benchmarks,
        )
    except OperacaoCancelada:
        logger.info(
            "Performance: processamento cancelado; resultado descartado"
        )
        return
    _registrar_resumo(payload)
    _gravar_snapshot(payload, ref_date, config, snapshot_store)
    logger.info(
        "Performance: processamento concluído (%d benchmarks)",
        len(payload["results"]),
    )
    ctx.resultado(valor=payload)


def _processar(
    ctx: JobContext,
    caso: AnalyzePerformanceUseCase,
    cache: PerformanceCache,
    current_data: Mapping[str, object],
    classificacao: Mapping[str, str],
    tickers: Sequence[str],
    ref_date: date,
    config: SamplingConfig,
    benchmarks: Sequence[str],
) -> dict:
    """Executa o read-through do cache e calcula os benchmarks faltantes."""
    resultados = ler_cache(
        cache, benchmarks, classificacao, ref_date,
        config.period_days, config.method,
    )
    faltantes = [b for b in benchmarks if b not in resultados]
    logger.info(
        "Performance: cache reutilizado=%s; a calcular=%s",
        sorted(resultados),
        faltantes,
    )
    if faltantes:
        ctx.raise_if_cancelled()
        calculados = caso.execute(
            current_data, classificacao, ref_date, benchmarks=faltantes
        )
        gravar_cache(
            cache, calculados, classificacao, ref_date,
            config.period_days, config.method,
        )
        resultados.update(calculados)
    return montar_payload(resultados, classificacao, benchmarks, tickers)


def _gravar_snapshot(
    payload: dict,
    ref_date: date,
    config: SamplingConfig,
    snapshot_store: object | None,
) -> None:
    """Grava o snapshot estável, quando houver um store configurado."""
    if snapshot_store is None:
        return
    snapshot = montar_snapshot(
        payload,
        ref_date=ref_date,
        period_days=config.period_days,
        sampling_method=config.method,
        source=SOURCE_GUI,
    )
    gravado = snapshot_store.gravar(snapshot)  # type: ignore[attr-defined]
    if gravado is False:
        logger.warning(
            "Performance: snapshot não gravado; mantendo o resultado em memória"
        )


def _registrar_resumo(payload: dict) -> None:
    """Registra no log o resumo por benchmark do payload produzido."""
    for benchmark, resultado in payload.get("results", {}).items():
        logger.info(
            "Performance %s: %d tickers elegíveis, índice disponível=%s",
            benchmark,
            len(resultado.get("tickers", [])),
            resultado.get("index_available", True),
        )
