"""Preço de fechamento B3 a partir dos dados de negociação já carregados.

Satisfaz o ``MarketPricePort`` reutilizando o campo ``LastPric`` dos dados B3
existentes, sem novo adapter de mercado. Retorna o último fechamento válido
cuja data é menor ou igual à data de referência.
"""

from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from flowscope.domain.entities import TradeDay
from flowscope.domain.fii.analysis import PrecoObservacao

FONTE_B3 = "B3"


class B3MarketPricePort:
    """Último fechamento (``LastPric``) por ticker nos dados B3 carregados."""

    def __init__(self: "B3MarketPricePort", negociacoes: list[TradeDay]) -> None:
        """Indexa as negociações informadas por ticker."""
        self._por_ticker: dict[str, list[TradeDay]] = {}
        for negociacao in negociacoes:
            ticker = negociacao.ticker.value
            self._por_ticker.setdefault(ticker, []).append(negociacao)
        for lista in self._por_ticker.values():
            lista.sort(key=lambda item: item.date)

    def preco_fechamento(
        self: "B3MarketPricePort", ticker: str, reference_date: date
    ) -> PrecoObservacao | None:
        """Retorna o último fechamento válido até a data de referência."""
        normalizado = ticker.strip().upper()
        candidatos = self._por_ticker.get(normalizado, [])
        ultimo: TradeDay | None = None
        for negociacao in candidatos:
            if negociacao.date <= reference_date and negociacao.last_price.value > 0:
                ultimo = negociacao
        if ultimo is None:
            return None
        return PrecoObservacao(
            preco=ultimo.last_price.value,
            data_preco=ultimo.date,
            fonte=FONTE_B3,
        )


class B3MarketPriceFromResult:
    """Último fechamento por ticker a partir do resultado diário da análise.

    Satisfaz o ``MarketPricePort`` reutilizando o campo ``last_price`` dos dados
    diários já carregados, sem novo acesso de mercado.
    """

    def __init__(
        self: "B3MarketPriceFromResult",
        daily_data: Mapping[str, list[dict]],
    ) -> None:
        """Indexa os dados diários informados por ticker."""
        self._por_ticker = {
            ticker.upper(): dias for ticker, dias in daily_data.items()
        }

    def preco_fechamento(
        self: "B3MarketPriceFromResult", ticker: str, reference_date: date
    ) -> PrecoObservacao | None:
        """Retorna o último fechamento válido até a data de referência."""
        normalizado = ticker.strip().upper()
        candidatos = self._por_ticker.get(normalizado, [])
        ultimo: tuple[date, Decimal] | None = None
        for dia in candidatos:
            data = dia.get("date")
            preco = dia.get("last_price")
            if data is None or preco is None:
                continue
            valor = Decimal(str(preco))
            if data <= reference_date and valor > 0:
                ultimo = (data, valor)
        if ultimo is None:
            return None
        return PrecoObservacao(
            preco=ultimo[1],
            data_preco=ultimo[0],
            fonte=FONTE_B3,
        )
