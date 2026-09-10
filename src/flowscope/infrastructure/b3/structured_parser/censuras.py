"""Extração de censuras públicas do HTML estático da B3."""

import re

from bs4 import Tag

from flowscope.domain.structured import CensuraPublica
from flowscope.infrastructure.b3.structured_parser.html_utils import parse_html

_TICKER_RE = re.compile(r"\(([A-Z0-9]+)\)")
_DATA_CENSURA_RE = re.compile(r"\(?(\d{2}/\d{2}/\d{4})\)?")


def extrair_censuras(html: str) -> list[CensuraPublica]:
    """Extrai as censuras públicas do HTML estático da B3."""
    soup = parse_html(html)
    censuras: list[CensuraPublica] = []
    blocos = soup.find_all("div", class_="item-censura")
    if not blocos:
        blocos = soup.find_all(
            "div", class_=lambda valor: valor and "censura" in str(valor)
        )
    for bloco in blocos:
        censura = _extrair_censura_do_bloco(bloco)
        if censura is not None:
            censuras.append(censura)
    return censuras


def _extrair_censura_do_bloco(bloco: Tag) -> CensuraPublica | None:
    """Extrai uma censura pública de um bloco ``div.item-censura``."""
    titulo, ticker = _titulo_e_ticker_do_bloco(bloco)
    conteudo = _conteudo_do_bloco(bloco)
    if not titulo and not conteudo:
        return None
    return CensuraPublica(
        titulo=titulo,
        ticker=ticker,
        data=_data_do_bloco(bloco),
        conteudo=conteudo,
    )


def _titulo_e_ticker_do_bloco(bloco: Tag) -> tuple[str, str | None]:
    """Extrai o título e o ticker do bloco de censura."""
    titulo_tag = bloco.find("h3") or bloco.find(["h2", "h4"]) or bloco.find("strong")
    titulo = titulo_tag.get_text(" ", strip=True) if titulo_tag else ""
    match_ticker = _TICKER_RE.search(titulo)
    ticker = match_ticker.group(1) if match_ticker else None
    return titulo, ticker


def _data_do_bloco(bloco: Tag) -> str:
    """Extrai a data da censura do bloco, com fallback no texto completo."""
    data_tag = bloco.find(
        "span", class_=lambda valor: valor and "data" in str(valor)
    )
    data = None
    if data_tag is not None:
        data = _data_em_texto(data_tag.get_text(" ", strip=True))
    if data is None:
        data = _data_em_texto(bloco.get_text(" ", strip=True))
    return data or ""


def _conteudo_do_bloco(bloco: Tag) -> str:
    """Extrai o conteúdo descritivo do primeiro parágrafo do bloco."""
    paragrafo = bloco.find("p")
    if paragrafo is None:
        return ""
    return paragrafo.get_text(" ", strip=True)


def _data_em_texto(texto: str) -> str | None:
    """Extrai uma data ``DD/MM/AAAA`` de um texto."""
    match = _DATA_CENSURA_RE.search(texto)
    if match is None:
        return None
    return match.group(1)
