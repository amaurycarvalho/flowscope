"""Preço de fechamento B3 a partir dos dados de negociação já carregados.

Satisfaz o ``MarketPricePort`` reutilizando o campo ``LastPric`` dos dados B3
existentes, sem novo adapter de mercado. Retorna o último fechamento válido
cuja data é menor ou igual à data de referência.
"""

from datetime import date

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
