"""Consulta cache-only dos títulos normalizados de um ticker."""

from __future__ import annotations

from flowscope.application.renda_fixa.portas import TitulosRepository
from flowscope.domain.renda_fixa import CarteiraTitulos


class ConsultarTitulosUseCase:
    """Lê a carteira de títulos do cache, sem acessar a rede."""

    def __init__(
        self: ConsultarTitulosUseCase, repositorio: TitulosRepository
    ) -> None:
        """Guarda o repositório de leitura do cache."""
        self._repositorio = repositorio

    def executar(
        self: ConsultarTitulosUseCase, ticker: str
    ) -> CarteiraTitulos | None:
        """Retorna a carteira em cache do ticker, ou ``None``."""
        if not ticker:
            return None
        return self._repositorio.ler(ticker)
