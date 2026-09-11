"""Aquisição tolerante de dados fundamentalistas por ticker."""

import logging
from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_fields import _decimal_campo
from flowscope.application.fundamental_ports import (
    CAMPO_DIVIDENDO_POR_COTA,
    CAMPO_PATRIMONIO,
    CampoFundamental,
    OrigemDados,
)
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
