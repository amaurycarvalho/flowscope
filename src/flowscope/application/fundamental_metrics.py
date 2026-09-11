"""Cálculo de métricas fundamentalistas (FFO, DY e P/VP)."""

from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_fields import _fontes
from flowscope.domain.fii import (
    MetricasFii,
    PatrimonioFii,
    PrecoObservacao,
    Quality,
    analisar_snapshot,
)
from flowscope.domain.fii.metrics import FiiSnapshot


def _p_vp_de(
    preco: PrecoObservacao, patrimonio: PatrimonioFii | None
) -> tuple[Decimal | None, Decimal | None]:
    """Deriva o valor de mercado e o P/VP a partir do preço e do patrimônio."""
    if patrimonio is None or patrimonio.net_asset_value <= 0:
        return None, None
    market_value = preco.preco * patrimonio.shares_outstanding
    return market_value, market_value / patrimonio.net_asset_value


class FundamentalMetricsMixin:
    """Mixin com o cálculo das métricas FFO e parciais por ticker."""

    def _metricas_parciais(
        self: "FundamentalMetricsMixin",
        ticker: str,
        reference_date: date,
        dividendos_12m_por_cota: Decimal | None,
        patrimonio: PatrimonioFii | None = None,
        preco: PrecoObservacao | None = None,
    ) -> MetricasFii | None:
        """Calcula Dividend Yield e P/VP sem exigir dados de FFO."""
        if self._mercado is None:
            return None
        if preco is None:
            preco = self._mercado.preco_fechamento(ticker, reference_date)
        if preco is None or preco.preco <= 0:
            return None
        if patrimonio is None:
            patrimonio = self._repository.obter_patrimonio(ticker, reference_date)
        dividend_yield = (
            dividendos_12m_por_cota / preco.preco
            if dividendos_12m_por_cota is not None
            else None
        )
        market_value, p_vp = _p_vp_de(preco, patrimonio)
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
        self: "FundamentalMetricsMixin",
        ticker: str,
        reference_date: date,
        dividendos_12m_por_cota: Decimal | None,
        patrimonio: PatrimonioFii | None = None,
        preco: PrecoObservacao | None = None,
    ) -> MetricasFii | None:
        """Calcula as métricas FFO quando a fonte fornecer os dados."""
        if self._ffo_provider is None or self._mercado is None:
            return None
        if patrimonio is None:
            patrimonio = self._repository.obter_patrimonio(ticker, reference_date)
        ffo = self._ffo_provider.obter_ffo(ticker, reference_date)
        if preco is None:
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
