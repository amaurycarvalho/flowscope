"""Caso de uso da análise fundamentalista por ticker da watchlist.

Orquestra as etapas identidade → classificação → dividendos → (Fase B)
métricas FFO, mantendo cada ticker isolado: a falha de um ticker não invalida
os demais (RFC-007 §73).
"""

import logging
from collections.abc import Callable
from datetime import date, datetime, timezone

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
    TaxonomiaFii,
    classificar_cotistas,
    classificar_patrimonio,
    classificar_ticker,
    dividendos_12m,
    normalizar_ticker,
    percentual_preco_tipico,
    preco_tipico,
)

logger = logging.getLogger("flowscope")


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
        cotacao = _decimal_campo(dados, CAMPO_COTACAO)
        exibicao = _classificacao_exibicao(dados, classificacao)
        tipico = preco_tipico(
            _decimal_campo(dados, CAMPO_MAX_52_SEM),
            _decimal_campo(dados, CAMPO_MIN_52_SEM),
            cotacao,
        )
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
            data_referencia=_data_campo(dados, CAMPO_DATA_REFERENCIA),
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
