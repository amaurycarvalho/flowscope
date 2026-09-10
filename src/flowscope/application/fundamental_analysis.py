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
    CAMPO_DATA_REFERENCIA,
    CAMPO_DISCRIMINADOR,
    CAMPO_DIVIDEND_YIELD,
    CAMPO_DIVIDENDO_POR_COTA,
    CAMPO_ESPECIE,
    CAMPO_FFO_TREND,
    CAMPO_FFO_YIELD,
    CAMPO_GESTAO,
    CAMPO_NOME,
    CAMPO_P_FFO,
    CAMPO_P_VP,
    CAMPO_PATRIMONIO,
    CAMPO_QTD_IMOVEIS,
    CAMPO_SEGMENTO,
    CAMPO_SETOR,
    CAMPO_SUBSETOR,
    CampoFundamental,
    DividendHistoryProvider,
    FfoProvider,
    FiiFundamentalRepository,
    FundamentalDataProvider,
    MarketPricePort,
    OrigemDados,
)
from flowscope.domain.fii import (
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    DividendoConsolidado,
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
    calcular_ultimo_dividendo_consolidado,
    classificar_cotistas,
    classificar_exibicao,
    classificar_patrimonio,
    classificar_tendencia_ffo,
    classificar_ticker,
    consolidar_dividendos,
    dividendos_12m,
    dividendos_de_proventos,
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
        historico_dividendos: DividendHistoryProvider | None = None,
    ) -> None:
        """Inicializa o caso de uso com as portas de dados."""
        self._repository = repository
        self._ffo_provider = ffo_provider
        self._mercado = mercado
        self._taxonomia = taxonomia_fii
        self._fundamental_provider = fundamental_provider
        self._historico_dividendos = historico_dividendos
        self.houve_atualizacao = False
        self.houve_falha_recuperavel = False

    def execute(
        self: "FundamentalAnalysisUseCase",
        tickers: list[str],
        reference_date: date | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
    ) -> list[AnaliseFundamental]:
        """Analisa cada ticker de forma isolada e retorna uma linha por ativo."""
        referencia = reference_date or datetime.now(timezone.utc).date()
        self.houve_atualizacao = False
        self.houve_falha_recuperavel = False
        resultados: list[AnaliseFundamental] = []
        total = len(tickers)
        for indice, ticker in enumerate(tickers, start=1):
            normalizado = normalizar_ticker(ticker)
            try:
                resultado, de_cache = self._analisar_ticker(normalizado, referencia)
                if progress_callback is not None:
                    detalhe = f"Fundamentos: {normalizado} ({indice}/{total})"
                    if de_cache:
                        detalhe += " - cached"
                    progress_callback(detalhe, False)
                resultados.append(resultado)
            except Exception as exc:
                self.houve_falha_recuperavel = True
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
    ) -> tuple[AnaliseFundamental, bool]:
        """Analisa um único ticker da identidade às métricas FFO.

        Retorna a análise e se os dados vieram do cache.
        """
        classificacao = classificar_ticker(
            ticker, taxonomia_fii=self._taxonomia
        )
        dados, de_cache = self._obter_dados(ticker, reference_date)
        nome = _texto(dados, CAMPO_NOME) or self._repository.obter_nome(ticker)
        proventos = self._repository.obter_proventos(ticker, reference_date)
        ultimo_dividendo = self._ultimo_dividendo(
            dados, ticker, reference_date, proventos
        )
        total_por_cota = (
            dividendos_12m(proventos, reference_date) if proventos else None
        )
        patrimonio_repo = self._repository.obter_patrimonio(ticker, reference_date)
        patrimonio = _decimal_campo(dados, CAMPO_PATRIMONIO)
        if patrimonio is None and patrimonio_repo is not None:
            patrimonio = patrimonio_repo.net_asset_value
        cotistas = patrimonio_repo.cotistas if patrimonio_repo is not None else None
        metricas = _metricas_dos_dados(dados)
        if metricas is None:
            metricas = self._analisar_ffo(
                ticker, reference_date, total_por_cota, patrimonio_repo
            )
        if metricas is None:
            metricas = self._metricas_parciais(
                ticker, reference_date, total_por_cota, patrimonio_repo
            )
        avisos = _avisos_ffo_ausente(metricas)
        return AnaliseFundamental(
            ticker=ticker,
            nome=nome,
            classificacao=classificacao,
            ultimo_dividendo=ultimo_dividendo,
            dividendos_12m_por_cota=total_por_cota,
            metricas=metricas,
            classificacao_exibicao=_classificacao_exibicao(dados, classificacao),
            cotistas=cotistas,
            patrimonio=patrimonio,
            classe_cotistas=(
                classificar_cotistas(cotistas) if cotistas is not None else None
            ),
            classe_patrimonio=(
                classificar_patrimonio(patrimonio)
                if patrimonio is not None
                else None
            ),
            data_referencia=_data_campo(dados, CAMPO_DATA_REFERENCIA),
            avisos=avisos,
        ), de_cache

    def _obter_dados(
        self: "FundamentalAnalysisUseCase", ticker: str, reference_date: date
    ) -> tuple[dict[str, CampoFundamental], bool]:
        """Obtém os campos fundamentalistas compostos, tolerando falhas.

        Retorna os campos e se a origem foi o cache.
        """
        if self._fundamental_provider is None:
            return {}, False
        obter_com_resultado = getattr(
            self._fundamental_provider, "obter_com_resultado", None
        )
        try:
            if callable(obter_com_resultado):
                campos, origem = obter_com_resultado(ticker, reference_date)
                if origem is OrigemDados.REDE:
                    self.houve_atualizacao = True
                return campos, origem is OrigemDados.CACHE
            return self._fundamental_provider.obter(ticker, reference_date), False
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter dados fundamentalistas de %s",
                ticker,
                exc_info=True,
            )
            return {}, False

    def _ultimo_dividendo(
        self: "FundamentalAnalysisUseCase",
        dados: dict[str, CampoFundamental],
        ticker: str,
        reference_date: date,
        proventos: list,
    ) -> UltimoDividendo:
        """Consolida B3, CVM e Fundamentus e calcula o último dividendo."""
        b3 = dividendos_de_proventos(proventos, "B3")
        consolidados = consolidar_dividendos(
            b3, self._dividendos_secundarios(ticker, reference_date)
        )
        if not consolidados:
            valor = _decimal_campo(dados, CAMPO_DIVIDENDO_POR_COTA)
            if valor is not None:
                consolidados = [
                    DividendoConsolidado(
                        data_base=None, valor=valor, fonte="FUNDAMENTUS"
                    )
                ]
        return calcular_ultimo_dividendo_consolidado(consolidados, reference_date)

    def _dividendos_secundarios(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
    ) -> list[DividendoConsolidado]:
        """Obtém o histórico secundário (ex.: CVM), tolerando indisponibilidade."""
        if self._historico_dividendos is None:
            return []
        try:
            return list(
                self._historico_dividendos.obter_dividendos(ticker, reference_date)
            )
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter histórico de dividendos de %s",
                ticker,
                exc_info=True,
            )
            return []

    def _metricas_parciais(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        dividendos_12m_por_cota: Decimal | None,
        patrimonio: PatrimonioFii | None = None,
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
        if patrimonio is None:
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
        dividendos_12m_por_cota: Decimal | None,
        patrimonio: PatrimonioFii | None = None,
    ) -> MetricasFii | None:
        """Calcula as métricas FFO quando a fonte fornecer os dados."""
        if self._ffo_provider is None or self._mercado is None:
            return None
        if patrimonio is None:
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


def _avisos_ffo_ausente(metricas: MetricasFii | None) -> tuple[str, ...]:
    """Retorna os avisos quando as métricas FFO esperadas não foram calculadas."""
    if metricas is None:
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


def _int_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> int | None:
    """Retorna o valor inteiro de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    try:
        return int(campo.valor)
    except (TypeError, ValueError):
        return None


def _data_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> date | None:
    """Retorna o valor de data de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None:
        return None
    valor = campo.valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            return None
    return None


def _classificacao_exibicao(
    dados: dict[str, CampoFundamental], fallback: ClassificacaoAtivo | None
) -> ClassificacaoExibicao:
    """Compõe Tipo/Sub-tipo a partir dos campos do Fundamentus, com fallback."""
    return classificar_exibicao(
        discriminador=_texto(dados, CAMPO_DISCRIMINADOR),
        especie=_texto(dados, CAMPO_ESPECIE),
        setor=_texto(dados, CAMPO_SETOR),
        subsetor=_texto(dados, CAMPO_SUBSETOR),
        segmento=_texto(dados, CAMPO_SEGMENTO),
        gestao=_texto(dados, CAMPO_GESTAO),
        qtd_imoveis=_int_campo(dados, CAMPO_QTD_IMOVEIS),
        fallback=fallback,
    )


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
