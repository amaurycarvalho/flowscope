"""Parser do Informe Mensal Estruturado da B3 (RFC-008 §13-16).

O documento do FundosNet é HTML tabular com linhas ``rótulo → valor``. O
parsing é orientado por rótulo e tolerante a acentuação e ao sobrescrito
``¹``; campos ausentes resultam em ausência de valor, sem invalidar o restante.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from flowscope.domain.b3 import B3InformeMensal
from flowscope.infrastructure.fii.parsing import moeda_para_decimal

#: Fonte registrada nos informes extraídos.
FONTE_B3 = "B3"

_ROTULOS_COTISTAS = ("numerodecotistas",)
_ROTULOS_PATRIMONIO = ("patrimonioliquido", "patrimonioliquidor")
_ROTULOS_COTAS = ("numerodecotasemitidas",)
_ROTULOS_VP_COTA = ("valorpatrimonialdascotas", "valorpatrimonialdascotasr")

_TROCA_ACENTOS = {
    "á": "a",
    "à": "a",
    "â": "a",
    "ã": "a",
    "é": "e",
    "ê": "e",
    "í": "i",
    "ó": "o",
    "ô": "o",
    "õ": "o",
    "ú": "u",
    "ç": "c",
}


def extrair_informe_mensal(
    html: str,
    *,
    document_id: int,
    reference_date: date | None = None,
    reference_month: str | None = None,
    fonte: str = FONTE_B3,
) -> B3InformeMensal:
    """Monta o informe mensal a partir do HTML do documento FundosNet."""
    pares = _coletar_pares(html)
    return B3InformeMensal(
        document_id=document_id,
        reference_date=reference_date,
        reference_month=reference_month,
        cotistas=_inteiro(_valor(pares, _ROTULOS_COTISTAS)),
        patrimonio_liquido=_decimal(_valor(pares, _ROTULOS_PATRIMONIO)),
        cotas_emitidas=_decimal(_valor(pares, _ROTULOS_COTAS)),
        valor_patrimonial_cota=_decimal(_valor(pares, _ROTULOS_VP_COTA)),
        fonte=fonte,
    )


def _coletar_pares(html: str) -> dict[str, str]:
    """Mapeia ``rótulo normalizado → valor`` para todos os pares de células."""
    soup = BeautifulSoup(html, "html.parser")
    pares: dict[str, str] = {}
    for linha in soup.find_all("tr"):
        celulas = [
            celula.get_text(" ", strip=True)
            for celula in linha.find_all(["td", "th"])
        ]
        for indice, texto in enumerate(celulas[:-1]):
            chave = _normalizar(texto)
            if not chave or chave in pares:
                continue
            valor = celulas[indice + 1].strip()
            if valor:
                pares[chave] = valor
    return pares


def _normalizar(texto: str) -> str:
    """Normaliza um rótulo para letras minúsculas sem acentos."""
    resultado = texto.strip().lower()
    for origem, destino in _TROCA_ACENTOS.items():
        resultado = resultado.replace(origem, destino)
    return "".join(caractere for caractere in resultado if caractere.isalpha())


def _valor(pares: dict[str, str], rotulos: tuple[str, ...]) -> str | None:
    """Retorna o valor do primeiro rótulo presente no mapa de pares."""
    for chave, valor in pares.items():
        if chave in rotulos:
            return valor
    return None


def _inteiro(valor: str | None) -> int | None:
    """Interpreta o número de cotistas, ignorando separadores de milhar."""
    if not valor:
        return None
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return None
    try:
        return int(digitos)
    except ValueError:
        return None


def _decimal(valor: str | None) -> Decimal | None:
    """Interpreta um valor monetário brasileiro como ``Decimal``, ou ``None``."""
    if not valor:
        return None
    try:
        return moeda_para_decimal(valor)
    except (InvalidOperation, ValueError):
        return None
