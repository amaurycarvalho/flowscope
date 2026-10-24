"""Chaves determinísticas e identificadores curtos dos títulos.

A chave de fonte é estável entre aquisições e usa apenas dados da fonte. O
identificador do caminho é o SHA-1 truncado da chave, evitando nomes brutos com
barras, acentos e tamanho variável.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

#: Caracteres que não podem compor uma parte da chave de fonte.
_CARACTERES_INVALIDOS = re.compile(r"[|\x00\r\n]")

#: CNPJ genérico usado por fontes para "não informado".
_CNPJ_GENERICO = "00000000000000"


def _parte(valor: object) -> str:
    """Normaliza uma parte da chave, recusando separadores e controles."""
    texto = "" if valor is None else str(valor).strip()
    if _CARACTERES_INVALIDOS.search(texto):
        raise ValueError(f"caractere inválido na chave de fonte: {texto!r}")
    return texto


def chave_fonte(partes: Iterable[object]) -> str:
    """Monta a chave de fonte determinística a partir das partes informadas."""
    return "|".join(_parte(parte) for parte in partes)


def id_curto(chave: str) -> str:
    """Retorna o identificador curto e estável de uma chave de fonte."""
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()[:10]


def _texto_data(valor: date | None) -> str:
    """Formata uma data opcional para a chave de fonte."""
    return valor.isoformat() if valor is not None else ""


def _texto_decimal(valor: Decimal | None) -> str:
    """Formata um decimal opcional para a chave de fonte, sem ruído."""
    if valor is None:
        return ""
    return format(valor.normalize(), "f")


def chave_fre(
    cnpj: str,
    valor_mobiliario: str,
    identificacao: str,
    data_emissao: date | None,
    data_vencimento: date | None,
    quantidade: Decimal | None,
    valor: Decimal | None,
) -> str:
    """Monta a chave estável de uma linha do FRE."""
    return chave_fonte(
        (
            cnpj,
            valor_mobiliario,
            identificacao,
            _texto_data(data_emissao),
            _texto_data(data_vencimento),
            _texto_decimal(quantidade),
            _texto_decimal(valor),
        )
    )


def chave_securit(
    codigo_cetip: str | None,
    codigo_isin: str | None,
    cnpj_emissora: str | None,
    codigo_identificacao: str | None,
) -> str:
    """Monta a chave estável de um CRI/CRA no SECURIT."""
    if codigo_cetip:
        return chave_fonte((codigo_cetip,))
    if codigo_isin:
        return chave_fonte((codigo_isin,))
    return chave_fonte((cnpj_emissora or "", codigo_identificacao or ""))


def chave_fii(
    codigo_cetip: str | None,
    cnpj_emissor: str | None,
    emissao: str | None,
    serie: str | None,
    data_vencimento: date | None,
) -> str:
    """Monta a chave estável de uma posição da carteira de FII."""
    if codigo_cetip:
        return chave_fonte((codigo_cetip,))
    return chave_fonte(
        (
            cnpj_emissor or "",
            emissao or "",
            serie or "",
            _texto_data(data_vencimento),
        )
    )


def chave_agregado(papel: str, tipo: str, ticker: str) -> str:
    """Monta a chave estável de um agregado por ticker."""
    return chave_fonte(("agregado", papel, tipo, ticker))


def cnpj_valido(cnpj: str | None) -> bool:
    """Valida um CNPJ de 14 dígitos, recusando vazio, genérico e dígitos ruins."""
    digitos = re.sub(r"\D", "", cnpj or "")
    if len(digitos) != 14 or digitos == _CNPJ_GENERICO:
        return False
    if len(set(digitos)) == 1:
        return False
    return _digito_verificador(digitos[:12]) == digitos[12] and _digito_verificador(
        digitos[:13]
    ) == digitos[13]


def _digito_verificador(base: str) -> str:
    """Calcula um dígito verificador do CNPJ pelo módulo 11."""
    pesos = (
        6,
        5,
        4,
        3,
        2,
        9,
        8,
        7,
        6,
        5,
        4,
        3,
        2,
    )
    deslocamento = len(pesos) - len(base)
    soma = sum(int(digito) * pesos[i + deslocamento] for i, digito in enumerate(base))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)
