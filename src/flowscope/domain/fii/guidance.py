"""Value object do guidance de distribuição de rendimentos de FIIs.

Representa o valor (ou faixa) projetado por cota, o período de validade e a
proveniência (data e caminho do Relatório Gerencial que apontou o guidance).
Um valor único é representado com ``valor_min == valor_max``.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Guidance:
    """Guidance de distribuição por cota com período e proveniência."""

    valor_min: Decimal
    valor_max: Decimal
    periodo: str
    data_relatorio: date
    caminho_pdf: str | None = None
