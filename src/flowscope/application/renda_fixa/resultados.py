"""Resultados da aquisição de títulos e das fontes normalizadas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from flowscope.domain.renda_fixa import (
    FonteTitulos,
    TituloAgregado,
    TituloRendaFixa,
)


@dataclass(frozen=True)
class ResultadoFontes:
    """Dados normalizados devolvidos por uma fonte, com falhas isoladas."""

    obrigacoes: tuple[TituloRendaFixa, ...] = ()
    direitos: tuple[TituloRendaFixa, ...] = ()
    agregados: tuple[TituloAgregado, ...] = ()
    fontes: dict[str, FonteTitulos] = field(default_factory=dict)
    falhas: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ResultadoAquisicaoTitulos:
    """Desfecho da aquisição de títulos de um ticker."""

    novos: int = 0
    atualizados: int = 0
    reutilizados: int = 0
    falhas: int = 0
    sem_cnpj: bool = False
    data_referencia: date | None = None
    obrigacoes: int = 0
    direitos: int = 0

    @property
    def adquiridos(self: ResultadoAquisicaoTitulos) -> int:
        """Total de itens persistidos na aquisição corrente."""
        return self.novos + self.atualizados + self.reutilizados


@dataclass(frozen=True)
class ResultadoInferencia:
    """Desfecho próprio da fase de inferência de direitos e obrigações."""

    executada: bool = False
    itens: int = 0
    falhas: int = 0
    cancelada: bool = False

    def para_dict(self: ResultadoInferencia) -> dict:
        """Serializa o desfecho para o JSON da CLI."""
        return {
            "executada": self.executada,
            "itens": self.itens,
            "falhas": self.falhas,
            "cancelada": self.cancelada,
        }
