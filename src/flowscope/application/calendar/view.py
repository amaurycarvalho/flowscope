"""Modelo puro da árvore ano/mês/dia da aba ``Feriados``."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date

from flowscope.domain.calendar import Holiday

MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)
_DIAS = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


@dataclass(frozen=True)
class FeriadoDia:
    """Folha de dia da árvore."""

    data: date
    nome: str
    origem: str

    @property
    def rotulo(self: FeriadoDia) -> str:
        """Return ``DD (abreviatura)`` for the tree leaf."""
        return f"{self.data.day:02d} ({_DIAS[self.data.weekday()]})"


@dataclass(frozen=True)
class FeriadoMes:
    """Ramo de mês da árvore."""

    mes: int
    dias: tuple[FeriadoDia, ...]

    @property
    def nome(self: FeriadoMes) -> str:
        """Return the Portuguese month name."""
        return MESES[self.mes - 1]


@dataclass(frozen=True)
class FeriadoAno:
    """Ramo de ano da árvore."""

    ano: int
    meses: tuple[FeriadoMes, ...]


def _dia(holiday: Holiday) -> FeriadoDia:
    return FeriadoDia(holiday.date, holiday.name, holiday.source)


def construir_arvore(
    anos: Mapping[int, Iterable[Holiday]],
) -> tuple[FeriadoAno, ...]:
    """Build the year/month/day tree with deterministic ordering."""
    arvores: list[FeriadoAno] = []
    for ano in sorted(anos, reverse=True):
        por_mes: dict[int, list[FeriadoDia]] = {}
        for holiday in anos[ano]:
            por_mes.setdefault(holiday.date.month, []).append(_dia(holiday))
        meses = tuple(
            FeriadoMes(mes, tuple(sorted(dias, key=lambda item: item.data.day)))
            for mes, dias in sorted(por_mes.items())
        )
        if meses:
            arvores.append(FeriadoAno(ano, meses))
    return tuple(arvores)


def texto_ano(ano: FeriadoAno) -> str:
    """Render the year selection as month-grouped holiday lines."""
    linhas = [str(ano.ano), ""]
    for mes in ano.meses:
        linhas.append(mes.nome)
        linhas.extend(f"  {dia.rotulo} {dia.nome}" for dia in mes.dias)
        linhas.append("")
    return "\n".join(linhas).rstrip() + "\n"


def texto_mes(mes: FeriadoMes) -> str:
    """Render the month selection day by day."""
    linhas = [mes.nome, ""]
    linhas.extend(f"{dia.rotulo} {dia.nome}" for dia in mes.dias)
    return "\n".join(linhas) + "\n"


def texto_dia(dia: FeriadoDia) -> str:
    """Render a single holiday with its date and origin."""
    return (
        f"{dia.data.isoformat()} ({_DIAS[dia.data.weekday()]}) — {dia.nome}"
        f" ({dia.origem})\n"
    )


def feriados_do_payload(payload: Mapping[str, object]) -> tuple[Holiday, ...]:
    """Convert a ``listar_ano`` payload into domain holidays."""
    itens = payload.get("feriados", [])
    if not isinstance(itens, list):
        return ()
    holidays: list[Holiday] = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        try:
            holidays.append(Holiday(
                date.fromisoformat(str(item["data"])),
                str(item["nome"]),
                str(item.get("origem", "ANBIMA")),
            ))
        except (KeyError, ValueError):
            continue
    return tuple(holidays)


__all__ = [
    "MESES",
    "FeriadoAno",
    "FeriadoDia",
    "FeriadoMes",
    "construir_arvore",
    "feriados_do_payload",
    "texto_ano",
    "texto_dia",
    "texto_mes",
]
