"""Adaptador da camada B3 para a porta ``FundamentalDataProvider``.

Atua como fallback de campos básicos (nome) quando a fonte primária não os
fornece, reutilizando a identidade resolvida na B3.
"""

from datetime import date

from flowscope.application.fundamental_ports import CAMPO_NOME, CampoFundamental
from flowscope.infrastructure.fii.b3_fundamental_repository import (
    B3FundamentalRepository,
)

#: Fonte registrada nos campos produzidos pelo adaptador.
FONTE_B3 = "B3"


class B3FundamentalDataProvider:
    """Fornece campos fundamentalistas básicos a partir da camada B3."""

    def __init__(
        self: "B3FundamentalDataProvider",
        repository: B3FundamentalRepository | None = None,
    ) -> None:
        """Inicializa o adaptador com o repositório fundamentalista B3."""
        self._repository = repository or B3FundamentalRepository()

    def obter(
        self: "B3FundamentalDataProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna o nome do fundo quando disponível na B3."""
        nome = self._repository.obter_nome(ticker)
        if nome:
            return {CAMPO_NOME: CampoFundamental(nome, FONTE_B3)}
        return {}
