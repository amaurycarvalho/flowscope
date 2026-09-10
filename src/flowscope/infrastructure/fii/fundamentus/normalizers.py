"""Normalizadores dos valores textuais do Fundamentus para tipos do domínio."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

_NUM_RE = re.compile(r"-?\d[\d.]*(?:,\d+)?")
_VAZIOS = {"", "-", "--"}


def para_decimal(texto: str | None) -> Decimal | None:
    """Interpreta um número/percentual brasileiro como ``Decimal``.

    Aceita formatos como ``R$ 691.996.000.000``, ``1.234,56`` e ``-0,08%``.
    Células vazias ou contendo apenas ``-`` retornam ``None``.
    """
    if texto is None:
        return None
    limpo = texto.strip().replace("\xa0", " ")
    if limpo in _VAZIOS:
        return None
    limpo = limpo.replace("%", "").replace("R$", "").strip()
    match = _NUM_RE.search(limpo)
    if match is None:
        return None
    bruto = match.group(0)
    if "," in bruto:
        inteiro, _, decimal = bruto.partition(",")
        normalizado = f"{inteiro.replace('.', '') or '0'}.{decimal}"
    else:
        normalizado = bruto.replace(".", "")
    try:
        return Decimal(normalizado)
    except InvalidOperation:
        return None


def para_int(texto: str | None) -> int | None:
    """Interpreta um número inteiro, retornando ``None`` quando inválido."""
    valor = para_decimal(texto)
    if valor is None:
        return None
    try:
        return int(valor)
    except (ValueError, OverflowError):
        return None


def para_data(texto: str | None) -> date | None:
    """Interpreta uma data no formato ``DD/MM/AAAA`` (ou ``DD/MM/AA``)."""
    if not texto:
        return None
    partes = texto.strip().split("/")
    if len(partes) != 3:
        return None
    try:
        dia, mes, ano = (int(parte) for parte in partes)
    except ValueError:
        return None
    if ano < 100:
        ano += 2000
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None
