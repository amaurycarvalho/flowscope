"""Extração de censuras públicas do HTML estático da B3."""

import re

from bs4 import Tag

from flowscope.domain.structured import CensuraPublica
from flowscope.infrastructure.b3.structured_parser.html_utils import parse_html

_TICKER_RE = re.compile(r"\(([A-Z0-9]+)\)")
_DATA_CENSURA_RE = re.compile(r"\(?(\d{2}/\d{2}/\d{4})\)?")
_TITULO_DATA_RE = re.compile(r"^(.*?)\s*\((\d{2}/\d{2}/\d{4})\)\s*$")


def extrair_censuras(html: str) -> list[CensuraPublica]:
    """Extrai as censuras públicas do HTML estático da B3.

    A página real lista as censuras em ``li.accordion-navigation`` (âncora com
    emissor, ticker e data, e o conteúdo em parágrafos). O formato antigo de
    ``div.item-censura`` continua aceito como fallback.
    """
    soup = parse_html(html)
    blocos = soup.find_all("li", class_="accordion-navigation")
    if blocos:
        return [
            censura
            for censura in (_extrair_censura_accordion(bloco) for bloco in blocos)
            if censura is not None
        ]
    legados = soup.find_all(
        "div", class_=lambda valor: valor and "item-censura" in str(valor)
    )
    return [
        censura
        for censura in (_extrair_censura_do_bloco(bloco) for bloco in legados)
        if censura is not None
    ]


def _extrair_censura_accordion(bloco: Tag) -> CensuraPublica | None:
    """Extrai uma censura de um item ``li.accordion-navigation``."""
    ancora = bloco.find("a")
    texto = ancora.get_text(" ", strip=True) if ancora is not None else ""
    titulo, data = _titulo_e_data(texto)
    conteudo = _conteudo_completo_do_bloco(bloco)
    if not titulo and not conteudo:
        return None
    if not data:
        data = _data_em_texto(bloco.get_text(" ", strip=True)) or ""
    return CensuraPublica(
        titulo=titulo,
        ticker=_ticker_do_titulo(titulo),
        data=data,
        conteudo=conteudo,
    )


def _titulo_e_data(texto: str) -> tuple[str, str]:
    """Separa o título da data final entre parênteses, quando houver."""
    match = _TITULO_DATA_RE.match(texto)
    if match is None:
        return texto.strip(), ""
    return match.group(1).strip(), match.group(2)


def _ticker_do_titulo(titulo: str) -> str | None:
    """Extrai o ticker entre parênteses do título, quando houver."""
    match = _TICKER_RE.search(titulo)
    return match.group(1) if match is not None else None


def _conteudo_completo_do_bloco(bloco: Tag) -> str:
    """Concatena os parágrafos do bloco em um único conteúdo."""
    paragrafos = [
        paragrafo.get_text(" ", strip=True)
        for paragrafo in bloco.find_all("p")
    ]
    return "\n".join(texto for texto in paragrafos if texto)


def _extrair_censura_do_bloco(bloco: Tag) -> CensuraPublica | None:
    """Extrai uma censura pública do formato legado ``div.item-censura``."""
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
    return titulo, _ticker_do_titulo(titulo)


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
