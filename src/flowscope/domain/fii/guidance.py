"""Value objects do guidance de distribuição de rendimentos de FIIs.

Representa o valor (ou faixa) projetado por cota, o período de validade e a
proveniência (data e caminho do Relatório Gerencial que apontou o guidance).
Um valor único é representado com ``valor_min == valor_max``. A avaliação de um
Relatório Gerencial é registrada por :class:`AvaliacaoGuidance`, que guarda o
método usado e o resultado (guidance ou ausência avaliada).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

#: Método de avaliação por IA.
METODO_IA = "ia"

#: Método de avaliação determinística (expressões regulares).
METODO_DETERMINISTICO = "deterministico"


@dataclass(frozen=True)
class Guidance:
    """Guidance de distribuição por cota com período e proveniência."""

    valor_min: Decimal
    valor_max: Decimal
    periodo: str
    data_relatorio: date
    caminho_pdf: str | None = None


@dataclass(frozen=True)
class AvaliacaoGuidance:
    """Resultado da avaliação de um Relatório Gerencial.

    ``guidance`` é ``None`` quando a avaliação concluiu que o relatório não
    contém guidance de distribuição; nesse caso a entrada existe apenas para
    marcar o relatório como avaliado pelo ``metodo`` informado.
    """

    metodo: str
    data_relatorio: date
    caminho_pdf: str | None = None
    guidance: Guidance | None = None

    @property
    def tem_guidance(self: "AvaliacaoGuidance") -> bool:
        """Indica se a avaliação encontrou guidance."""
        return self.guidance is not None
