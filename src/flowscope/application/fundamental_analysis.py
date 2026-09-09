"""Caso de uso da análise fundamentalista por ticker da watchlist.

Orquestra as etapas identidade → classificação → dividendos → (Fase B)
métricas FFO, mantendo cada ticker isolado: a falha de um ticker não invalida
os demais (RFC-007 §73).
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    FfoProvider,
    FiiFundamentalRepository,
    MarketPricePort,
)
from flowscope.domain.fii import (
    FfoObservacao,
    Inconsistencia,
    MetricasFii,
    PatrimonioFii,
    PrecoObservacao,
    TaxonomiaFii,
    TendenciaDividendo,
    UltimoDividendo,
    analisar_snapshot,
    calcular_ultimo_dividendo,
    classificar_ticker,
    dividendos_12m,
    normalizar_ticker,
)
from flowscope.domain.fii.analysis import AnaliseFundamental
from flowscope.domain.fii.metrics import FiiSnapshot

logger = logging.getLogger("flowscope")


def _sem_dividendo() -> UltimoDividendo:
    """Retorna um resultado de dividendo vazio (N/A)."""
    return UltimoDividendo(
        data_com=None,
        valor=None,
        valor_anterior=None,
        tendencia=TendenciaDividendo.N_A,
    )


class FundamentalAnalysisUseCase:
    """Analisa tickers da watchlist e produz uma linha por ativo."""

    def __init__(
        self: "FundamentalAnalysisUseCase",
        repository: FiiFundamentalRepository,
        ffo_provider: FfoProvider | None = None,
        mercado: MarketPricePort | None = None,
        taxonomia_fii: TaxonomiaFii | None = None,
    ) -> None:
        """Inicializa o caso de uso com as portas de dados."""
        self._repository = repository
        self._ffo_provider = ffo_provider
        self._mercado = mercado
        self._taxonomia = taxonomia_fii

    def execute(
        self: "FundamentalAnalysisUseCase",
        tickers: list[str],
        reference_date: date | None = None,
    ) -> list[AnaliseFundamental]:
        """Analisa cada ticker de forma isolada e retorna uma linha por ativo."""
        referencia = reference_date or datetime.now(timezone.utc).date()
        resultados: list[AnaliseFundamental] = []
        for ticker in tickers:
            normalizado = normalizar_ticker(ticker)
            try:
                resultados.append(self._analisar_ticker(normalizado, referencia))
            except Exception as exc:
                logger.warning("Falha ao analisar %s: %s", normalizado, exc)
                resultados.append(
                    AnaliseFundamental(
                        ticker=normalizado,
                        nome=None,
                        classificacao=classificar_ticker(
                            normalizado, taxonomia_fii=self._taxonomia
                        ),
                        ultimo_dividendo=_sem_dividendo(),
                        dividendos_12m_por_cota=None,
                        metricas=None,
                        avisos=(),
                        erro=str(exc),
                    )
                )
        return resultados

    def _analisar_ticker(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
    ) -> AnaliseFundamental:
        """Analisa um único ticker da identidade às métricas FFO."""
        classificacao = classificar_ticker(
            ticker, taxonomia_fii=self._taxonomia
        )
        nome = self._repository.obter_nome(ticker)
        proventos = self._repository.obter_proventos(ticker, reference_date)
        ultimo_dividendo = calcular_ultimo_dividendo(proventos, reference_date)
        total_por_cota = (
            dividendos_12m(proventos, reference_date) if proventos else None
        )
        metricas = self._analisar_ffo(
            ticker,
            reference_date,
            classificacao.elegivel_ffo(),
            total_por_cota,
        )
        avisos = _avisos_ffo_ausente(metricas, classificacao.elegivel_ffo())
        return AnaliseFundamental(
            ticker=ticker,
            nome=nome,
            classificacao=classificacao,
            ultimo_dividendo=ultimo_dividendo,
            dividendos_12m_por_cota=total_por_cota,
            metricas=metricas,
            avisos=avisos,
        )

    def _analisar_ffo(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        elegivel: bool,
        dividendos_12m_por_cota: Decimal | None,
    ) -> MetricasFii | None:
        """Calcula as métricas FFO apenas para FIIs elegíveis com dados."""
        if not elegivel:
            return None
        if self._ffo_provider is None or self._mercado is None:
            return None
        patrimonio = self._repository.obter_patrimonio(ticker, reference_date)
        ffo = self._ffo_provider.obter_ffo(ticker, reference_date)
        preco = self._mercado.preco_fechamento(ticker, reference_date)
        if (
            patrimonio is None
            or ffo is None
            or preco is None
            or dividendos_12m_por_cota is None
        ):
            return None
        dividendos_totais = (
            dividendos_12m_por_cota * patrimonio.shares_outstanding
        )
        snapshot = FiiSnapshot(
            ticker=ticker,
            reference_date=reference_date,
            price=preco.preco,
            shares_outstanding=patrimonio.shares_outstanding,
            net_asset_value=patrimonio.net_asset_value,
            ffo_12m=ffo.ffo_12m,
            ffo_3m=ffo.ffo_3m,
            dividends_12m=dividendos_totais,
        )
        fontes = _fontes(ffo, patrimonio, preco)
        return analisar_snapshot(snapshot, fontes=fontes)


def _avisos_ffo_ausente(metricas: MetricasFii | None, elegivel: bool) -> tuple[str, ...]:
    """Retorna os avisos quando métricas FFO esperadas não foram calculadas."""
    if elegivel and metricas is None:
        return (Inconsistencia.FFO_NOT_AVAILABLE.value,)
    return ()


def _fontes(
    ffo: FfoObservacao,
    patrimonio: PatrimonioFii,
    preco: PrecoObservacao,
) -> tuple[str, ...]:
    """Combina as fontes dos dados que alimentaram o snapshot."""
    return (ffo.fonte, patrimonio.fonte, preco.fonte)
