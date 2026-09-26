"""Preparação dos dados do gráfico de ranking de dominância.

Contém as funções puras de construção das linhas do ranking e dos
comprimentos das hastes de volume; o posicionamento dos rótulos dos
tickers permanece na apresentação.
"""

from dataclasses import dataclass
from datetime import date

from flowscope.application.dominance.hastes import stem_length


@dataclass(frozen=True)
class RankingRow:
    """Último CLV e fluxo monetário de um ativo no ranking de dominância."""

    ticker: str
    clv: float
    mfv: float
    date: date


def build_rows(data: dict) -> list[RankingRow]:
    """Extrai as linhas do ranking a partir dos dados brutos do pregão.

    Cada linha guarda o último CLV e o fluxo monetário de cada ativo,
    ignorando ativos sem indicadores de CLV disponíveis.
    """
    rows: list[RankingRow] = []
    for ticker, info in data.items():
        clv_dict = info.get("all_indicators", {}).get("clv")
        if not clv_dict:
            continue
        last_date = max(clv_dict.keys())
        clv = clv_dict[last_date]
        if clv is None:
            continue
        mfv = info.get("money_flow_volume")
        rows.append(RankingRow(
            ticker=ticker,
            clv=float(clv),
            mfv=float(mfv) if mfv is not None else 0.0,
            date=last_date,
        ))
    return rows


def stem_lengths(
    mfvs: list[float],
    max_val: float,
    scale: float = 0.10,
) -> list[float]:
    """Calcula o comprimento da haste de volume de cada linha do ranking."""
    return [stem_length(mfv, max_val, scale) for mfv in mfvs]
