"""Caso de uso da análise fundamentalista por ticker da watchlist.

Orquestra as etapas identidade → classificação → dividendos → (Fase B)
métricas FFO, mantendo cada ticker isolado: a falha de um ticker não invalida
os demais (RFC-007 §73).
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import TypeVar

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
    CAMPO_FFO_3M,
    CAMPO_FFO_12M,
    CAMPO_GESTOR,
    CAMPO_LPA,
    CAMPO_MAX_52_SEM,
    CAMPO_MIN_52_SEM,
    CAMPO_NOME,
    CAMPO_QTD_IMOVEIS,
    CAMPO_RECEITA_3M,
    CAMPO_RECEITA_12M,
    CAMPO_RENDIMENTOS_3M,
    CAMPO_RENDIMENTOS_12M,
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
    FundamentalHistoryStore,
    IndexadoresProvider,
    MarketPricePort,
    observacao_completa,
)
from flowscope.application.fundamental_providers import FundamentalDataMixin
from flowscope.domain.bdr import DadosBdr
from flowscope.domain.fii import (
    TIPO_EXIBICAO_FII,
    AnaliseFundamental,
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    DividendoConsolidado,
    MargensFii,
    MetricasFii,
    PatrimonioFii,
    PrecoObservacao,
    Quality,
    ResolverFiagro,
    TaxonomiaFii,
    TipoAtivo,
    UltimoDividendo,
    classe_fii_elegivel_ffo,
    classificar_cotistas,
    classificar_patrimonio,
    classificar_ticker,
    dividendos_12m,
    dividendos_ffo,
    dividendos_receita,
    ffo_receita,
    normalizar_ticker,
    p_l_bdr,
    percentual_preco_tipico,
    preco_tipico,
    tendencia_margem_ffo,
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
        historico_store: FundamentalHistoryStore | None = None,
        resolver_fiagro: ResolverFiagro | None = None,
        bdr_provider: object | None = None,
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
        self._historico_store = historico_store
        self._resolver_fiagro = resolver_fiagro
        self._bdr_provider = bdr_provider
        self.houve_atualizacao = False
        self.houve_falha_recuperavel = False

    def execute(
        self: "FundamentalAnalysisUseCase",
        tickers: list[str],
        reference_date: date | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        force_refresh: bool = False,
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
                resultado, de_cache = self._analisar_ou_cache(
                    normalizado, referencia, force_refresh
                )
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
                            normalizado,
                            taxonomia_fii=self._taxonomia,
                            resolver_fiagro=self._resolver_fiagro,
                        ),
                        ultimo_dividendo=_sem_dividendo(),
                        dividendos_12m_por_cota=None,
                        metricas=None,
                        avisos=(),
                        erro=str(exc),
                    )
                )
        return resultados

    def _analisar_ou_cache(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        force_refresh: bool,
    ) -> tuple[AnaliseFundamental, bool]:
        """Serve a observação completa do dia ou analisa e registra no histórico.

        O acerto do dia exige uma observação completa e na versão de schema
        atual; observações parciais são recomputadas para poderem ser
        substituídas por uma melhor no mesmo dia.
        """
        if self._historico_store is not None and not force_refresh:
            observacao = self._historico_store.obter(ticker, reference_date)
            if observacao is not None and observacao_completa(observacao):
                return observacao, True
        resultado, de_cache = self._analisar_ticker(ticker, reference_date)
        self._registrar_observacao(ticker, reference_date, resultado, force_refresh)
        return resultado, de_cache

    def _registrar_observacao(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        resultado: AnaliseFundamental,
        force_refresh: bool,
    ) -> None:
        """Registra a observação no histórico quando a análise não falhou."""
        if self._historico_store is None or resultado.erro is not None:
            return
        self._historico_store.registrar(
            ticker, reference_date, resultado, force=force_refresh
        )

    def _analisar_ticker(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
    ) -> tuple[AnaliseFundamental, bool]:
        """Analisa um único ticker da identidade às métricas FFO.

        Retorna a análise e se os dados vieram do cache.
        """
        classificacao = classificar_ticker(
            ticker,
            taxonomia_fii=self._taxonomia,
            resolver_fiagro=self._resolver_fiagro,
        )
        dados, de_cache = self._obter_dados(ticker, reference_date)
        dados_bdr = self._obter_dados_bdr(ticker, reference_date, classificacao)
        nome = _resolver_nome(dados, ticker, dados_bdr, self._repository)
        exibicao = _classificacao_exibicao(dados, classificacao)
        proventos = self._repository.obter_proventos(ticker, reference_date)
        ultimo_dividendo = self._ultimo_dividendo(
            dados,
            ticker,
            reference_date,
            proventos,
            _dividendos_bdr(dados_bdr),
        )
        total_por_cota = _dividendos_12m(proventos, reference_date)
        patrimonio_repo = self._repository.obter_patrimonio(ticker, reference_date)
        patrimonio, cotistas = self._resolver_cotistas(
            ticker, reference_date, dados, classificacao, patrimonio_repo
        )
        cotas = self._resolver_cotas(dados, classificacao, patrimonio_repo)
        preco = self._obter_preco(ticker, reference_date)
        metricas = self._resolver_metricas(
            ticker,
            reference_date,
            total_por_cota,
            dados,
            classificacao,
            patrimonio_repo,
            preco,
        )
        avisos = _avisos_ffo_ausente(metricas)
        cotacao = _resolver_cotacao(dados, preco)
        if classificacao.tipo is TipoAtivo.BDR:
            metricas = _metricas_bdr(metricas, cotacao, ultimo_dividendo)
        else:
            metricas = _recalcular_dividend_yield(
                metricas, exibicao, cotacao, ultimo_dividendo
            )
        margens = _montar_margens(dados, exibicao)
        maximo, minimo = _extremos_52_sem(
            self._mercado, dados, ticker, reference_date
        )
        tipico = preco_tipico(maximo, minimo, cotacao)
        data_referencia = _resolver_data_referencia(dados, preco)
        return AnaliseFundamental(
            ticker=ticker,
            nome=nome,
            classificacao=classificacao,
            ultimo_dividendo=ultimo_dividendo,
            dividendos_12m_por_cota=total_por_cota,
            metricas=metricas,
            margens=margens,
            cotacao=cotacao,
            vp_cota=_decimal_campo(dados, CAMPO_VP_COTA),
            p_l=_resolver_p_l(
                classificacao, cotacao, ultimo_dividendo, dados, exibicao
            ),
            classificacao_exibicao=exibicao,
            cotas=cotas,
            cotistas=cotistas,
            patrimonio=patrimonio,
            classe_cotistas=_classificar_se_presente(
                cotistas, classificar_cotistas
            ),
            classe_patrimonio=_classificar_se_presente(
                patrimonio, classificar_patrimonio
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
            bdr_nivel=_campo_bdr(dados_bdr, "nivel_programa"),
            bdr_observacao=_campo_bdr(dados_bdr, "observacao"),
            nome_depositario=_campo_bdr(dados_bdr, "nome_depositario"),
            nome_empresa_bdr=_campo_bdr(dados_bdr, "nome_empresa"),
            isin=_campo_bdr(dados_bdr, "isin"),
            avisos=avisos,
        ), de_cache

    def _resolver_metricas(
        self: "FundamentalAnalysisUseCase",
        ticker: str,
        reference_date: date,
        total_por_cota: Decimal | None,
        dados: dict[str, CampoFundamental],
        classificacao: ClassificacaoAtivo,
        patrimonio_repo: PatrimonioFii | None,
        preco: PrecoObservacao | None,
    ) -> MetricasFii | None:
        """Resolve as métricas, tentando FFO antes das parciais."""
        metricas = _metricas_dos_dados(dados)
        if metricas is None and _elegivel_ffo(dados, classificacao):
            metricas = self._analisar_ffo(
                ticker, reference_date, total_por_cota, patrimonio_repo, preco
            )
        if metricas is None:
            metricas = self._metricas_parciais(
                ticker, reference_date, total_por_cota, patrimonio_repo, preco
            )
        return metricas

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


def _recalcular_dividend_yield(
    metricas: MetricasFii | None,
    exibicao: ClassificacaoExibicao,
    cotacao: Decimal | None,
    ultimo_dividendo: UltimoDividendo,
) -> MetricasFii | None:
    """Recalcula o Dividend Yield de FII como ``(último dividendo × 12) / cotação``.

    Mantém as métricas originais (Fundamentus e fallbacks) quando o ativo é
    ``Papel`` ou quando o último dividendo/cotação não está disponível.
    """
    if metricas is None or exibicao.tipo != TIPO_EXIBICAO_FII:
        return metricas
    valor = ultimo_dividendo.valor
    if valor is None or cotacao is None or cotacao == Decimal(0):
        return metricas
    return replace(metricas, dividend_yield=(valor * Decimal(12)) / cotacao)


#: Trimestres usados para anualizar o dividendo de um BDR.
_TRIMESTRES_ANO_BDR = Decimal(4)


def _metricas_bdr(
    metricas: MetricasFii | None,
    cotacao: Decimal | None,
    ultimo_dividendo: UltimoDividendo,
) -> MetricasFii | None:
    """Recalcula o Dividend Yield de BDR como ``(último dividendo × 4) / cotação``.

    Mantém as métricas originais quando o último dividendo ou a cotação estão
    ausentes ou a cotação é zero.
    """
    valor = ultimo_dividendo.valor
    if valor is None or cotacao is None or cotacao == Decimal(0):
        return metricas
    dividend_yield = (valor * _TRIMESTRES_ANO_BDR) / cotacao
    if metricas is None:
        return MetricasFii(
            market_value=None,
            ffo_yield=None,
            dividend_yield=dividend_yield,
            p_ffo=None,
            p_vp=None,
            ffo_momentum=None,
            ffo_trend=None,
            ffo_trend_change=None,
            ffo_payout=None,
            quality=Quality.PARTIAL,
            warnings=(),
            evidence=(),
        )
    return replace(metricas, dividend_yield=dividend_yield)


_T = TypeVar("_T")
_R = TypeVar("_R")


def _classificar_se_presente(
    valor: _T | None, classificador: Callable[[_T], _R]
) -> _R | None:
    """Aplica ``classificador`` apenas quando ``valor`` está presente."""
    if valor is None:
        return None
    return classificador(valor)


def _resolver_nome(
    dados: dict[str, CampoFundamental],
    ticker: str,
    dados_bdr: DadosBdr | None,
    repository: FiiFundamentalRepository,
) -> str | None:
    """Resolve o nome de exibição, caindo para o BDR quando ausente."""
    nome = _texto(dados, CAMPO_NOME) or repository.obter_nome(ticker)
    if nome is None and dados_bdr is not None:
        return dados_bdr.nome_empresa
    return nome


def _dividendos_bdr(
    dados_bdr: DadosBdr | None,
) -> list[DividendoConsolidado] | None:
    """Lista os dividendos consolidados do BDR, ou ``None`` sem dados."""
    if dados_bdr is None:
        return None
    return list(dados_bdr.dividendos)


def _dividendos_12m(proventos: list, reference_date: date) -> Decimal | None:
    """Total de dividendos dos últimos 12 meses, se houver proventos."""
    if not proventos:
        return None
    return dividendos_12m(proventos, reference_date)


def _resolver_cotacao(
    dados: dict[str, CampoFundamental], preco: PrecoObservacao | None
) -> Decimal | None:
    """Usa a cotação do provedor e, na ausência, o preço de fechamento B3."""
    cotacao = _decimal_campo(dados, CAMPO_COTACAO)
    if cotacao is None and preco is not None:
        return preco.preco
    return cotacao


def _resolver_data_referencia(
    dados: dict[str, CampoFundamental], preco: PrecoObservacao | None
) -> date | None:
    """Usa a data do provedor e, na ausência, a data do preço de fechamento."""
    data_referencia = _data_campo(dados, CAMPO_DATA_REFERENCIA)
    if data_referencia is None and preco is not None:
        return preco.data_preco
    return data_referencia


def _resolver_p_l(
    classificacao: ClassificacaoAtivo,
    cotacao: Decimal | None,
    ultimo_dividendo: UltimoDividendo,
    dados: dict[str, CampoFundamental],
    exibicao: ClassificacaoExibicao,
) -> Decimal | None:
    """Calcula o P/L conforme o ativo seja BDR ou não."""
    if classificacao.tipo is TipoAtivo.BDR:
        return p_l_bdr(cotacao, ultimo_dividendo.valor)
    return _p_l_do_ativo(dados, exibicao, cotacao, ultimo_dividendo)


def _campo_bdr(dados_bdr: DadosBdr | None, atributo: str) -> str | None:
    """Lê um campo textual de identidade do BDR, ou ``None`` sem dados."""
    if dados_bdr is None:
        return None
    valor = getattr(dados_bdr, atributo)
    return valor if isinstance(valor, str) else None


def _montar_margens(
    dados: dict[str, CampoFundamental], exibicao: ClassificacaoExibicao
) -> MargensFii | None:
    """Monta as razões sobre a receita, apenas para tickers do tipo FII."""
    if exibicao.tipo != TIPO_EXIBICAO_FII:
        return None
    ffo_12m = _decimal_campo(dados, CAMPO_FFO_12M)
    ffo_3m = _decimal_campo(dados, CAMPO_FFO_3M)
    receita_12m = _decimal_campo(dados, CAMPO_RECEITA_12M)
    receita_3m = _decimal_campo(dados, CAMPO_RECEITA_3M)
    rendimentos_12m = _decimal_campo(dados, CAMPO_RENDIMENTOS_12M)
    rendimentos_3m = _decimal_campo(dados, CAMPO_RENDIMENTOS_3M)
    margem_12m = ffo_receita(ffo_12m, receita_12m)
    margem_3m = ffo_receita(ffo_3m, receita_3m)
    return MargensFii(
        ffo_receita_12m=margem_12m,
        ffo_receita_3m=margem_3m,
        dividendos_receita_12m=dividendos_receita(rendimentos_12m, receita_12m),
        dividendos_receita_3m=dividendos_receita(rendimentos_3m, receita_3m),
        dividendos_ffo_12m=dividendos_ffo(rendimentos_12m, ffo_12m),
        dividendos_ffo_3m=dividendos_ffo(rendimentos_3m, ffo_3m),
        ffo_trend=tendencia_margem_ffo(margem_12m.valor, margem_3m.valor),
    )
