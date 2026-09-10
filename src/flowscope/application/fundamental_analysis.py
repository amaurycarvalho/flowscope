"""Caso de uso da análise fundamentalista por ticker da watchlist.

Orquestra as etapas identidade → classificação → dividendos → (Fase B)
métricas FFO, mantendo cada ticker isolado: a falha de um ticker não invalida
os demais (RFC-007 §73).
"""

import logging
from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from flowscope.application.fundamental_ports import (
    CAMPO_DIVIDEND_YIELD,
    CAMPO_FFO_TREND,
    CAMPO_FFO_YIELD,
    CAMPO_NOME,
    CAMPO_P_FFO,
    CAMPO_P_VP,
    CampoFundamental,
    FfoProvider,
    FiiFundamentalRepository,
    FundamentalDataProvider,
    MarketPricePort,
)
from flowscope.domain.fii import (
    FfoObservacao,
    Inconsistencia,
    MetricasFii,
    PatrimonioFii,
    PrecoObservacao,
    Quality,
    TaxonomiaFii,
    TendenciaDividendo,
    UltimoDividendo,
    analisar_snapshot,
    calcular_ultimo_dividendo,
    classificar_tendencia_ffo,
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
        fundamental_provider: FundamentalDataProvider | None = None,
    ) -> None:
        """Inicializa o caso de uso com as portas de dados."""
        self._repository = repository
        self._ffo_provider = ffo_provider
        self._mercado = mercado
        self._taxonomia = taxonomia_fii
        self._fundamental_provider = fundamental_provider
        self.houve_atualizacao = False

    def execute(
        self: "FundamentalAnalysisUseCase",
        tickers: list[str],
        reference_date: date | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
    ) -> list[AnaliseFundamental]:
        """Analisa cada ticker de forma isolada e retorna uma linha por ativo."""
        referencia = reference_date or datetime.now(timezone.utc).date()
        self.houve_atualizacao = False
        resultados: list[AnaliseFundamental] = []
        total = len(tickers)
        for indice, ticker in enumerate(tickers, start=1):
            normalizado = normalizar_ticker(ticker)
            if progress_callback is not None:
                progress_callback(
                    f"Fundamentos: {normalizado} ({indice}/{total})", False
                )
            try:
                resultados.append(self._analisar_ticker(normalizado, referencia))
            except Exception as exc:
                logger.warning("Falha ao analisar %s: %s", normalizado, exc)
                if progress_callback is not None:
                    progress_callback(f"Falha em {normalizado}", True)
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
        dados = self._obter_dados(ticker, reference_date)
        nome = _texto(dados, CAMPO_NOME) or self._repository.obter_nome(ticker)
        proventos = self._repository.obter_proventos(ticker, reference_date)
        ultimo_dividendo = calcular_ultimo_dividendo(proventos, reference_date)
        total_por_cota = (
            dividendos_12m(proventos, reference_date) if proventos else None
        )
        elegivel = classificacao.elegivel_ffo()
        metricas = _metricas_dos_dados(dados) if elegivel else None
        if metricas is None:
            metricas = self._analisar_ffo(
                ticker,
                reference_date,
                elegivel,
                total_por_cota,
            )
        if metricas is None and elegivel:
            metricas = self._metricas_parciais(
                ticker, reference_date, total_por_cota
            )
        avisos = _avisos_ffo_ausente(metricas, elegivel)
        return AnaliseFundamental(
            ticker=ticker,
            nome=nome,
            classificacao=classificacao,
            ultimo_dividendo=ultimo_dividendo,
            dividendos_12m_por_cota=total_por_cota,
            metricas=metricas,
            avisos=avisos,
        )

    def _obter_dados(
        self: "FundamentalAnalysisUseCase", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Obtém os campos fundamentalistas compostos, tolerando falhas."""
        if self._fundamental_provider is None:
            return {}
        obter_com_resultado = getattr(
            self._fundamental_provider, "obter_com_resultado", None
        )
        try:
            if callable(obter_com_resultado):
                campos, atualizou = obter_com_resultado(ticker, reference_date)
                if atualizou:
                    self.houve_atualizacao = True
                return campos
            return self._fundamental_provider.obter(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter dados fundamentalistas de %s",
                ticker,
                exc_info=True,
            )
            return {}

    def _metricas_parciais(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        dividendos_12m_por_cota: Decimal | None,
    ) -> MetricasFii | None:
        """Calcula Dividend Yield e P/VP sem exigir dados de FFO."""
        if self._mercado is None:
            return None
        preco = self._mercado.preco_fechamento(ticker, reference_date)
        if preco is None or preco.preco <= 0:
            return None
        dividend_yield = (
            dividendos_12m_por_cota / preco.preco
            if dividendos_12m_por_cota is not None
            else None
        )
        patrimonio = self._repository.obter_patrimonio(ticker, reference_date)
        market_value: Decimal | None = None
        p_vp: Decimal | None = None
        if patrimonio is not None and patrimonio.net_asset_value > 0:
            market_value = preco.preco * patrimonio.shares_outstanding
            p_vp = market_value / patrimonio.net_asset_value
        if dividend_yield is None and p_vp is None:
            return None
        return MetricasFii(
            market_value=market_value,
            ffo_yield=None,
            dividend_yield=dividend_yield,
            p_ffo=None,
            p_vp=p_vp,
            ffo_momentum=None,
            ffo_trend=None,
            ffo_trend_change=None,
            ffo_payout=None,
            quality=Quality.PARTIAL,
            warnings=(),
            evidence=(),
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


def _texto(
    dados: dict[str, CampoFundamental], chave: str
) -> str | None:
    """Retorna o valor textual de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    return str(campo.valor)


def _decimal_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> Decimal | None:
    """Retorna o valor decimal de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    if isinstance(campo.valor, Decimal):
        return campo.valor
    try:
        return Decimal(str(campo.valor))
    except (InvalidOperation, ValueError):
        return None


def _metricas_dos_dados(
    dados: dict[str, CampoFundamental],
) -> MetricasFii | None:
    """Monta as métricas a partir dos campos reportados por uma fonte primária."""
    ffo_yield = _decimal_campo(dados, CAMPO_FFO_YIELD)
    dividend_yield = _decimal_campo(dados, CAMPO_DIVIDEND_YIELD)
    p_ffo = _decimal_campo(dados, CAMPO_P_FFO)
    p_vp = _decimal_campo(dados, CAMPO_P_VP)
    trend_change = _decimal_campo(dados, CAMPO_FFO_TREND)
    if all(
        valor is None
        for valor in (ffo_yield, dividend_yield, p_ffo, p_vp, trend_change)
    ):
        return None
    tendencia = (
        classificar_tendencia_ffo(trend_change)
        if trend_change is not None
        else None
    )
    qualidade = (
        Quality.COMPLETE
        if ffo_yield is not None and p_vp is not None
        else Quality.PARTIAL
    )
    return MetricasFii(
        market_value=None,
        ffo_yield=ffo_yield,
        dividend_yield=dividend_yield,
        p_ffo=p_ffo,
        p_vp=p_vp,
        ffo_momentum=trend_change,
        ffo_trend=tendencia,
        ffo_trend_change=trend_change,
        ffo_payout=None,
        quality=qualidade,
        warnings=(),
        evidence=(),
    )
