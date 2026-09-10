"""Extração de valores associados a rótulos textuais no HTML."""

import re

from bs4 import BeautifulSoup, Tag

from flowscope.infrastructure.b3.structured_parser.html_utils import (
    _normalizar,
    _texto_apos_no_parent,
    _texto_do_proximo_sibling,
)


def extrair_por_rotulo(soup: BeautifulSoup, rotulo: str) -> str | None:
    """Extrai o valor associado a um rótulo textual no HTML.

    Procura o texto do rótulo e captura o valor no mesmo elemento após os
    dois-pontos, no elemento seguinte (irmão) ou no texto restante do
    elemento pai. Retorna ``None`` quando o rótulo não é encontrado.
    """
    rotulo_normalizado = rotulo.strip().lower().rstrip(":")
    fragmento = rotulo.rstrip(":")
    elementos = soup.find_all(
        string=lambda text: fragmento.lower() in text.lower() if text else False
    )
    for elem in elementos:
        texto = str(elem).strip()
        if ":" in texto:
            valor = texto.split(":", 1)[1].strip()
            if valor:
                return valor
        parent = elem.parent
        if parent is None:
            continue
        if isinstance(parent, Tag):
            restante = _texto_apos_no_parent(parent, elem)
            if restante:
                return restante
        valor = _texto_do_proximo_sibling(parent)
        if valor and valor.lower() != rotulo_normalizado:
            return valor
    return None


def _rotulo_em_celula(celula: str) -> bool:
    """Indica se o texto da célula parece um rótulo de campo."""
    if ":" in celula:
        return True
    normalizada = _normalizar(celula)
    palavras = re.split(r"[^a-z0-9]+", normalizada)
    alvos = {
        "nomedofundo",
        "cnpj",
        "codigodenegociacao",
        "administrador",
        "isin",
        "datadainformacao",
        "ano",
        "database",
        "datadopagamento",
        "periododereferencia",
        "valordoprovento",
        "rendimento",
        "amortizacao",
        "tipodeprovento",
        "responsavelpelainformacao",
        "telefonecontato",
    }
    return any(palavra in alvos for palavra in palavras)


def _pares_rotulo_valor(cells: list[str]) -> dict[str, str]:
    """Agrupa as células de uma linha de tabela em pares rótulo→valor."""
    pares: dict[str, str] = {}
    idx = 0
    while idx < len(cells):
        rotulo = cells[idx]
        if _rotulo_em_celula(rotulo):
            if idx + 1 < len(cells):
                pares[rotulo.rstrip(":")] = cells[idx + 1]
            idx += 2
        else:
            idx += 1
    return pares
