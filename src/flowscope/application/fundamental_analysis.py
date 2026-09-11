"""Caso de uso da análise fundamentalista por ticker da watchlist.

Orquestra as etapas identidade → classificação → dividendos → (Fase B)
métricas FFO, mantendo cada ticker isolado: a falha de um ticker não invalida
os demais (RFC-007 §73).
"""

import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flowscope.application.fundamental_fields import (
    _avisos_ffo_ausente,
    _classificacao_exibicao,
    _data_campo,
    _decimal_campo,
    _int_campo,
    _metricas_dos_dados,
    _p_l_do_ativo,
    _sem_dividendo,
    _texto,
)
from flowscope.application.fundamental_metrics import FundamentalMetricsMixin
from flowscope.application.fundamental_ports import (
    CAMPO_ADMINISTRADOR,
    CAMPO_CAP_RATE,
    CAMPO_CLASSIFICACAO_FII,
    CAMPO_CNPJ,
    CAMPO_CNPJ_ADMINISTRADOR,
    CAMPO_CNPJ_GESTOR,
    CAMPO_COTACAO,
    CAMPO_DATA_REFERENCIA,
    CAMPO_GESTOR,
    CAMPO_LPA,
    CAMPO_MAX_52_SEM,
    CAMPO_MIN_52_SEM,
    CAMPO_NOME,
    CAMPO_QTD_IMOVEIS,
    CAMPO_ROE,
    CAMPO_ROIC,
    CAMPO_VACANCIA_MEDIA,
    CAMPO_VP_COTA,
    AcionistasProvider,
    CampoFundamental,
    DividendHistoryProvider,
    FfoProvider,
    FiiFundamentalRepository,
    FundamentalDataProvider,
    IndexadoresProvider,
    MarketPricePort,
)
from flowscope.application.fundamental_providers import FundamentalDataMixin
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClassificacaoAtivo,
    PrecoObservacao,
    TaxonomiaFii,
    classe_fii_elegivel_ffo,
    classificar_cotistas,
    classificar_patrimonio,
    classificar_ticker,
    dividendos_12m,
    normalizar_ticker,
    percentual_preco_tipico,
    preco_tipico,
)

logger = logging.getLogger("flowscope")

#: Janela de referência do Preço Típico (52 semanas).
_JANELA_52_SEMANAS = timedelta(weeks=52)


class FundamentalAnalysisUseCase(FundamentalDataMixin, FundamentalMetricsMixin):
    """Analisa tickers da watchlist e produz uma linha por ativo."""

    def __init__(
        self: "FundamentalAnalysisUseCase",
        repository: FiiFundamentalRepository,
        ffo_provider: FfoProvider | None = None,
        mercado: MarketPricePort | None = None,
        taxonomia_fii: TaxonomiaFii | None = None,
        fundamental_provider: FundamentalDataProvider | None = None,
        historico_dividendos: DividendHistoryProvider | None = None,
        acionistas_provider: AcionistasProvider | None = None,
        indexadores_provider: IndexadoresProvider | None = None,
    ) -> None:
        """Inicializa o caso de uso com as portas de dados."""
        self._repository = repository
        self._ffo_provider = ffo_provider
        self._mercado = mercado
        self._taxonomia = taxonomia_fii
        self._fundamental_provider = fundamental_provider
        self._historico_dividendos = historico_dividendos
        self._acionistas_provider = acionistas_provider
        self._indexadores_provider = indexadores_provider
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
        patrimonio, cotistas = self._resolver_cotistas(
            ticker, reference_date, dados, classificacao, patrimonio_repo
        )
        preco = self._obter_preco(ticker, reference_date)
        metricas = _metricas_dos_dados(dados)
        if metricas is None and _elegivel_ffo(dados, classificacao):
            metricas = self._analisar_ffo(
                ticker, reference_date, total_por_cota, patrimonio_repo, preco
            )
        if metricas is None:
            metricas = self._metricas_parciais(
                ticker, reference_date, total_por_cota, patrimonio_repo, preco
            )
        avisos = _avisos_ffo_ausente(metricas)
        cotacao = _decimal_campo(dados, CAMPO_COTACAO)
        if cotacao is None and preco is not None:
            cotacao = preco.preco
        exibicao = _classificacao_exibicao(dados, classificacao)
        maximo, minimo = _extremos_52_sem(
            self._mercado, dados, ticker, reference_date
        )
        tipico = preco_tipico(maximo, minimo, cotacao)
        data_referencia = _data_campo(dados, CAMPO_DATA_REFERENCIA)
        if data_referencia is None and preco is not None:
            data_referencia = preco.data_preco
        return AnaliseFundamental(
            ticker=ticker,
            nome=nome,
            classificacao=classificacao,
            ultimo_dividendo=ultimo_dividendo,
            dividendos_12m_por_cota=total_por_cota,
            metricas=metricas,
            cotacao=cotacao,
            vp_cota=_decimal_campo(dados, CAMPO_VP_COTA),
            p_l=_p_l_do_ativo(dados, exibicao, cotacao, ultimo_dividendo),
            classificacao_exibicao=exibicao,
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
            data_referencia=data_referencia,
            lpa=_decimal_campo(dados, CAMPO_LPA),
            roe=_decimal_campo(dados, CAMPO_ROE),
            roic=_decimal_campo(dados, CAMPO_ROIC),
            cap_rate=_decimal_campo(dados, CAMPO_CAP_RATE),
            vacancia_media=_decimal_campo(dados, CAMPO_VACANCIA_MEDIA),
            qtd_imoveis=_int_campo(dados, CAMPO_QTD_IMOVEIS),
            preco_tipico=tipico,
            pct_preco_tipico=percentual_preco_tipico(cotacao, tipico),
            indexadores=self._obter_indexadores(ticker, reference_date),
            cnpj=_texto(dados, CAMPO_CNPJ),
            nome_administrador=_texto(dados, CAMPO_ADMINISTRADOR),
            cnpj_administrador=_texto(dados, CAMPO_CNPJ_ADMINISTRADOR),
            nome_gestor=_texto(dados, CAMPO_GESTOR),
            cnpj_gestor=_texto(dados, CAMPO_CNPJ_GESTOR),
            avisos=avisos,
        ), de_cache

    def _obter_preco(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
    ) -> PrecoObservacao | None:
        """Obtém o último fechamento B3, ou ``None`` quando indisponível."""
        if self._mercado is None:
            return None
        return self._mercado.preco_fechamento(ticker, reference_date)


def _elegivel_ffo(
    dados: dict[str, CampoFundamental], classificacao: ClassificacaoAtivo
) -> bool:
    """Indica se o motor determinístico de FFO pode ser acionado.

    Deriva a classe efetiva da classificação autorregulação da B3 e, na sua
    ausência, da quantidade de imóveis do Fundamentus. FII de papel não é
    elegível; tickers sem informação permanecem elegíveis (comportamento
    anterior).
    """
    classe = classe_fii_elegivel_ffo(_texto(dados, CAMPO_CLASSIFICACAO_FII))
    if classe is not None:
        return classe
    qtd_imoveis = _int_campo(dados, CAMPO_QTD_IMOVEIS)
    if qtd_imoveis is not None:
        return qtd_imoveis > 0
    return classificacao.elegivel_ffo() or classificacao.sub_tipo is None


def _extremos_52_sem(
    mercado: MarketPricePort | None,
    dados: dict[str, CampoFundamental],
    ticker: str,
    reference_date: date,
) -> tuple[Decimal | None, Decimal | None]:
    """Resolve ``(máxima, mínima)`` de 52 semanas, com fallback da janela B3."""
    maximo = _decimal_campo(dados, CAMPO_MAX_52_SEM)
    minimo = _decimal_campo(dados, CAMPO_MIN_52_SEM)
    if maximo is not None and minimo is not None:
        return maximo, minimo
    extremos = getattr(mercado, "extremos_preco", None)
    if mercado is not None and callable(extremos):
        resultado = extremos(ticker, reference_date, _JANELA_52_SEMANAS)
        if resultado is not None:
            minimo_b3, maximo_b3 = resultado
            if minimo is None:
                minimo = minimo_b3
            if maximo is None:
                maximo = maximo_b3
    return maximo, minimo
