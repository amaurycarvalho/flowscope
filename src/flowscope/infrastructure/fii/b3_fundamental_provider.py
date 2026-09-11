"""Adaptador da camada B3 para a porta ``FundamentalDataProvider``.

Atua como fallback de campos básicos (nome) quando a fonte primária não os
fornece, reutilizando a identidade resolvida na B3.
"""

from datetime import date

from flowscope.application.fundamental_ports import (
    CAMPO_ADMINISTRADOR,
    CAMPO_CNPJ,
    CAMPO_CNPJ_ADMINISTRADOR,
    CAMPO_NOME,
    CampoFundamental,
)
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
        """Retorna nome e identidade fiscal do fundo quando disponíveis na B3."""
        campos: dict[str, CampoFundamental] = {}
        nome = self._repository.obter_nome(ticker)
        if nome:
            campos[CAMPO_NOME] = CampoFundamental(nome, FONTE_B3)
        informe = self._repository.obter_informe(ticker, reference_date)
        if informe is not None:
            _adicionar(campos, CAMPO_CNPJ, informe.cnpj)
            _adicionar(campos, CAMPO_ADMINISTRADOR, informe.nome_administrador)
            _adicionar(
                campos, CAMPO_CNPJ_ADMINISTRADOR, informe.cnpj_administrador
            )
        return campos


def _adicionar(
    campos: dict[str, CampoFundamental], chave: str, valor: object
) -> None:
    """Adiciona um campo com a fonte B3 quando o valor existe."""
    if valor is not None:
        campos[chave] = CampoFundamental(valor, FONTE_B3)
