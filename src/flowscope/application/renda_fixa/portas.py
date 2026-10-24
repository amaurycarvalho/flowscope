"""Portas da aquisição e consulta dos títulos de renda fixa."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from flowscope.application.renda_fixa.resultados import ResultadoFontes
from flowscope.domain.renda_fixa import CarteiraInferencias, CarteiraTitulos


class TitulosRepository(Protocol):
    """Persistência por ticker dos títulos normalizados."""

    def ler(self: TitulosRepository, ticker: str) -> CarteiraTitulos | None:
        """Retorna a carteira em cache, ou ``None`` quando ausente/corrompida."""
        ...

    def gravar(self: TitulosRepository, carteira: CarteiraTitulos) -> None:
        """Grava a carteira atomicamente."""
        ...


class InferenciasRepository(Protocol):
    """Persistência por ticker das inferências extraídas dos resumos."""

    def ler(self: InferenciasRepository, ticker: str) -> CarteiraInferencias | None:
        """Retorna as inferências em cache, ou ``None`` quando ausentes."""
        ...

    def gravar(self: InferenciasRepository, carteira: CarteiraInferencias) -> None:
        """Grava as inferências atomicamente."""
        ...


class FonteTitulos(Protocol):
    """Fonte de dados normalizados para a aquisição de títulos."""

    def obter(
        self: FonteTitulos,
        ticker: str,
        cnpj: str,
        tipo_ativo: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancelar: Callable[[], None] | None = None,
        anterior: CarteiraTitulos | None = None,
    ) -> ResultadoFontes:
        """Retorna as obrigações e direitos normalizados das fontes.

        ``anterior`` é o último cache válido do ticker e permite que a fonte
        reaproveite o resultado sem reprocessar datasets inalterados.
        """
        ...
