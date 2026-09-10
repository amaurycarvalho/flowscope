"""Conversão de valores monetários, datas e isenções de IR."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from flowscope.infrastructure.b3.structured_parser.html_utils import (
    _normalizar,
    _texto_apos_rotulo,
)


def limpar_valor_monetario(valor: str | None) -> Decimal | None:
    """Limpa uma string monetária brasileira em ``Decimal``."""
    if not valor:
        return None
    texto = valor.replace("R$", "").strip()
    if "," in texto:
        inteiro, _, decimal = texto.partition(",")
        decimal = decimal.replace(",", "")
        texto = f"{inteiro.replace('.', '')}.{decimal}"
    else:
        texto = texto.replace(",", "").replace(".", "")
    try:
        return Decimal(texto or "0")
    except InvalidOperation:
        return None


def converter_data_br_para_iso(data_br: str | None) -> str | None:
    """Normaliza uma data ``DD/MM/AAAA`` para o formato ISO."""
    if not data_br:
        return None
    try:
        return datetime.strptime(data_br.strip(), "%d/%m/%Y").date().isoformat()  # noqa: DTZ007
    except ValueError:
        return data_br.strip()


def extrair_isento_ir(soup: BeautifulSoup) -> bool:
    """Identifica se o provento é isento de IR buscando pelo rótulo indicado."""
    fragmento = "Rendimento isento de IR"
    marcadores = soup.find_all(
        string=lambda text: fragmento.lower() in text.lower() if text else False
    )
    for marcador in marcadores:
        texto_rotulo = str(marcador)
        valor = _texto_apos_rotulo(marcador, texto_rotulo)
        if valor is not None:
            normalizado = _normalizar(valor)
            if "sim" in normalizado and "nao" not in normalizado:
                return True
            if "nao" in normalizado:
                return False
    return False


def extrair_nota_isencao(soup: BeautifulSoup) -> str | None:
    """Extrai a nota de isenção de IR do rodapé do documento."""
    nota = soup.find(
        "p",
        string=lambda text: "Administradora declara" in text if text else False,
    )
    if nota is not None:
        return nota.get_text(strip=True)
    texto = soup.find(
        string=lambda text: "Administradora declara" in text if text else False
    )
    if texto is None:
        return None
    return texto.strip()


def extrair_por_regex(html: str, padrao: re.Pattern) -> str | None:
    """Extrai um valor por expressão regular como estratégia de fallback."""
    match = padrao.search(html)
    if match is None:
        return None
    return match.group(1).strip()
