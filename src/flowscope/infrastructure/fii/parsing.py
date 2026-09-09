"""Funções de parsing compartilhadas pelos adapters de dados FII."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

_MOEDA_RE = re.compile(r"[^\d,.-]")


def moeda_para_decimal(valor: str) -> Decimal:
    """Interpreta um valor monetário brasileiro como ``Decimal``."""
    limpo = _MOEDA_RE.sub("", valor)
    if not limpo:
        raise InvalidOperation(valor)
    if "," in limpo:
        inteiro, _, decimal = limpo.partition(",")
        inteiro = inteiro.replace(".", "")
        return Decimal(f"{inteiro or '0'}.{decimal}")
    return Decimal(limpo.replace(".", ""))


def data_brasileira(valor: str) -> date:
    """Interpreta uma data no formato DD/MM/AAAA."""
    dia, mes, ano = (int(parte) for parte in valor.strip().split("/"))
    return date(ano, mes, dia)
