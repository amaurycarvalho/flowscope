"""Preço de fechamento B3 a partir dos dados de negociação já carregados.

Satisfaz o ``MarketPricePort`` reutilizando o campo ``LastPric`` dos dados B3
existentes, sem novo adapter de mercado. Retorna o último fechamento válido
cuja data é menor ou igual à data de referência.
"""

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal

from flowscope.domain.entities import TradeDay
from flowscope.domain.fii.analysis import PrecoObservacao

FONTE_B3 = "B3"


def _extremos(
    dias: list[tuple[date, Decimal, Decimal]],
    reference_date: date,
    janela: timedelta,
) -> tuple[Decimal, Decimal] | None:
    """Calcula ``(mínimo, máximo)`` dos dias válidos dentro da janela."""
    inicio = reference_date - janela
    minimos: list[Decimal] = []
    maximos: list[Decimal] = []
    for data, minimo, maximo in dias:
        if data < inicio or data > reference_date:
            continue
        if minimo > 0:
            minimos.append(minimo)
        if maximo > 0:
            maximos.append(maximo)
    if not minimos or not maximos:
        return None
    return min(minimos), max(maximos)


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

    def extremos_preco(
        self: "B3MarketPricePort",
        ticker: str,
        reference_date: date,
        janela: timedelta,
    ) -> tuple[Decimal, Decimal] | None:
        """Retorna ``(mínimo, máximo)`` da janela de negociações em memória."""
        normalizado = ticker.strip().upper()
        dias = [
            (
                negociacao.date,
                negociacao.min_price.value,
                negociacao.max_price.value,
            )
            for negociacao in self._por_ticker.get(normalizado, [])
        ]
        return _extremos(dias, reference_date, janela)


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

    def extremos_preco(
        self: "B3MarketPriceFromResult",
        ticker: str,
        reference_date: date,
        janela: timedelta,
    ) -> tuple[Decimal, Decimal] | None:
        """Retorna ``(mínimo, máximo)`` da janela de dados diários em memória."""
        normalizado = ticker.strip().upper()
        dias: list[tuple[date, Decimal, Decimal]] = []
        for dia in self._por_ticker.get(normalizado, []):
            data = dia.get("date")
            minimo = dia.get("min_price")
            maximo = dia.get("max_price")
            if data is None or minimo is None or maximo is None:
                continue
            dias.append((data, Decimal(str(minimo)), Decimal(str(maximo))))
        return _extremos(dias, reference_date, janela)
