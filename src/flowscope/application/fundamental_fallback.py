"""Composição de fontes fundamentalistas com prioridade por campo.

O Fundamentus é a fonte primária por padrão; B3, CVM e o motor de FFO atuam
como fallback quando a fonte anterior falha ou não fornece um campo. Cada
campo resultante preserva a origem que o forneceu.
"""

import logging
from collections.abc import Sequence
from datetime import date

from flowscope.application.fundamental_ports import (
    CAMPOS_FUNDAMENTAIS,
    CampoFundamental,
    FundamentalDataProvider,
)

logger = logging.getLogger("flowscope")


class CompositeFundamentalProvider:
    """Resolve cada campo pela primeira fonte que o fornecer, em ordem."""

    def __init__(
        self: "CompositeFundamentalProvider",
        providers: Sequence[FundamentalDataProvider],
    ) -> None:
        """Inicializa o composto com as fontes na ordem de prioridade."""
        self._providers = tuple(providers)

    @property
    def providers(
        self: "CompositeFundamentalProvider",
    ) -> tuple[FundamentalDataProvider, ...]:
        """Retorna as fontes na ordem de prioridade configurada."""
        return self._providers

    def obter(
        self: "CompositeFundamentalProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Compõe os campos consultando as fontes por prioridade."""
        resultado: dict[str, CampoFundamental] = {}
        for provider in self._providers:
            if CAMPOS_FUNDAMENTAIS.issubset(resultado):
                break
            try:
                campos = provider.obter(ticker, reference_date)
            except Exception:  # fonte indisponível: segue para o fallback
                logger.warning(
                    "Fonte fundamentalista %s indisponível para %s",
                    type(provider).__name__,
                    ticker,
                    exc_info=True,
                )
                continue
            for chave, campo in campos.items():
                if chave not in resultado and campo.valor is not None:
                    resultado[chave] = campo
        return resultado
