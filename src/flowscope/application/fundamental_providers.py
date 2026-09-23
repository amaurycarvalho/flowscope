"""Aquisição tolerante de dados fundamentalistas por ticker."""

import logging
from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_fields import _decimal_campo
from flowscope.application.fundamental_ports import (
    CAMPO_COTAS_EMITIDAS,
    CAMPO_DIVIDENDO_POR_COTA,
    CAMPO_PATRIMONIO,
    CampoFundamental,
    OrigemDados,
)
from flowscope.domain.bdr import DadosBdr
from flowscope.domain.fii import (
    ClassificacaoAtivo,
    DividendoConsolidado,
    PatrimonioFii,
    TipoAtivo,
    UltimoDividendo,
    calcular_ultimo_dividendo_consolidado,
    consolidar_dividendos,
    dividendos_de_proventos,
)

logger = logging.getLogger("flowscope")


class FundamentalDataMixin:
    """Mixin com aquisição tolerante de dados, dividendos e acionistas."""

    def _obter_dados(
        self: "FundamentalDataMixin", ticker: str, reference_date: date
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
        self: "FundamentalDataMixin",
        dados: dict[str, CampoFundamental],
        ticker: str,
        reference_date: date,
        proventos: list,
        dividendos_bdr: list[DividendoConsolidado] | None = None,
    ) -> UltimoDividendo:
        """Consolida B3, CVM/Fundamentus e BDR e calcula o último dividendo."""
        b3 = dividendos_de_proventos(proventos, "B3")
        consolidados = consolidar_dividendos(
            b3,
            self._dividendos_secundarios(ticker, reference_date),
            list(dividendos_bdr or []),
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
        self: "FundamentalDataMixin",
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

    def _obter_dados_bdr(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
        classificacao: ClassificacaoAtivo,
    ) -> DadosBdr | None:
        """Obtém dividendos e identidade de BDR apenas para ativos BDR.

        A fonte é acionada exclusivamente para tickers classificados como BDR;
        falhas são toleradas e resultam em ``None`` sem interromper a análise.
        """
        if self._bdr_provider is None or classificacao.tipo is not TipoAtivo.BDR:
            return None
        obter = getattr(self._bdr_provider, "obter_dados_bdr", None)
        if not callable(obter):
            return None
        try:
            return obter(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter dados de BDR de %s", ticker, exc_info=True
            )
            return None

    def _obter_acionistas(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
    ) -> int | None:
        """Obtém a quantidade de acionistas do Papel, tolerando indisponibilidade."""
        if self._acionistas_provider is None:
            return None
        try:
            return self._acionistas_provider.obter_acionistas(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter acionistas de %s", ticker, exc_info=True
            )
            return None

    def _obter_free_float(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
    ) -> Decimal | None:
        """Obtém o *free float* do ativo, tolerando indisponibilidade."""
        if self._free_float_provider is None:
            return None
        obter = getattr(self._free_float_provider, "obter_free_float", None)
        if not callable(obter):
            return None
        try:
            return obter(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter free float de %s", ticker, exc_info=True
            )
            return None

    def _obter_acoes_alugadas(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
    ) -> Decimal | None:
        """Obtém as ações alugadas do ativo, tolerando indisponibilidade."""
        if self._short_interest_provider is None:
            return None
        obter = getattr(self._short_interest_provider, "obter_acoes_alugadas", None)
        if not callable(obter):
            return None
        try:
            return obter(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter ações alugadas de %s", ticker, exc_info=True
            )
            return None

    def _obter_volume_medio(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
    ) -> Decimal | None:
        """Obtém o volume médio diário das negociações em memória."""
        if self._mercado is None:
            return None
        obter = getattr(self._mercado, "volume_medio", None)
        if not callable(obter):
            return None
        try:
            return obter(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter volume médio de %s", ticker, exc_info=True
            )
            return None

    def _obter_indexadores(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
    ) -> dict[str, Decimal]:
        """Obtém os percentuais por indexador, tolerando indisponibilidade."""
        if self._indexadores_provider is None:
            return {}
        try:
            return dict(
                self._indexadores_provider.obter_indexadores(
                    ticker, reference_date
                )
            )
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter indexadores de %s", ticker, exc_info=True
            )
            return {}

    def _resolver_cotistas(
        self: "FundamentalDataMixin",
        ticker: str,
        reference_date: date,
        dados: dict[str, CampoFundamental],
        classificacao: ClassificacaoAtivo,
        patrimonio_repo: PatrimonioFii | None,
    ) -> tuple[Decimal | None, int | None]:
        """Resolve patrimônio e cotistas, recorrendo aos acionistas de ações."""
        patrimonio = _decimal_campo(dados, CAMPO_PATRIMONIO)
        if patrimonio is None and patrimonio_repo is not None:
            patrimonio = patrimonio_repo.net_asset_value
        cotistas = patrimonio_repo.cotistas if patrimonio_repo is not None else None
        if cotistas is None and classificacao.tipo is TipoAtivo.ACAO:
            cotistas = self._obter_acionistas(ticker, reference_date)
        return patrimonio, cotistas

    def _resolver_cotas(
        self: "FundamentalDataMixin",
        dados: dict[str, CampoFundamental],
        classificacao: ClassificacaoAtivo,
        patrimonio_repo: PatrimonioFii | None,
    ) -> Decimal | None:
        """Resolve a quantidade de cotas/ações emitidas por tipo de ativo.

        Para FII, prioriza a B3/CVM (via ``PatrimonioFii``) e usa o Fundamentus
        como fallback; para Papel, usa apenas o Fundamentus.
        """
        fundamentus = _decimal_campo(dados, CAMPO_COTAS_EMITIDAS)
        if classificacao.tipo is TipoAtivo.ACAO:
            return fundamentus
        repo = (
            patrimonio_repo.shares_outstanding
            if patrimonio_repo is not None
            else None
        )
        return repo if repo is not None else fundamentus
