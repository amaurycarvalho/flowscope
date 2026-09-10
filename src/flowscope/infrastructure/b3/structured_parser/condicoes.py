"""Extração de condições excepcionais do HTML tabular da B3."""

import logging

from flowscope.domain.structured import CondicaoExcepcional
from flowscope.infrastructure.b3.structured_parser.html_utils import (
    _valor_ou_none,
    parse_html,
)

logger = logging.getLogger(__name__)


def extrair_condicoes_excepcionais(html: str) -> list[CondicaoExcepcional]:
    """Extrai as condições excepcionais da tabela HTML da B3."""
    soup = parse_html(html)
    condicoes: list[CondicaoExcepcional] = []
    tabela = soup.find("table")
    if tabela is None:
        return []
    for row in tabela.find_all("tr"):
        if row.find("th") is not None:
            continue
        celulas = [td.get_text(" ", strip=True) for td in row.find_all("td")]
        if not celulas:
            continue
        if len(celulas) < 5:
            logger.warning(
                "Linha de condições excepcionais ignorada com %d colunas",
                len(celulas),
            )
            continue
        condicoes.append(
            CondicaoExcepcional(
                companhia=celulas[0] or "",
                segmento=_valor_ou_none(celulas[1]),
                condicao=celulas[2] or "",
                data_concessao=_valor_ou_none(celulas[3]),
                prazo=_valor_ou_none(celulas[4]),
            )
        )
    return condicoes
