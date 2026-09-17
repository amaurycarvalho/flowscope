"""Extração de dividendos de BDRs (Plantão B3 + PDFs de avisos da CVM)."""

from flowscope.infrastructure.b3.bdr.cache import PdfCache
from flowscope.infrastructure.b3.bdr.client import BdrClient
from flowscope.infrastructure.b3.bdr.constants import (
    MESES_JANELA,
    PARSER_VERSION,
)
from flowscope.infrastructure.b3.bdr.documents import (
    conteudo_e_pdf,
    decodificar_pdf,
    id_protocolo,
    resolver_url_documento,
)
from flowscope.infrastructure.b3.bdr.news import (
    filtrar_avisos,
    itens_de_noticias,
    janelas_mensais,
    listar_avisos,
    raiz_ticker,
)
from flowscope.infrastructure.b3.bdr.parser import parse_dividendo
from flowscope.infrastructure.b3.bdr.provider import BdrDividendProvider
from flowscope.infrastructure.b3.bdr.text import extrair_texto

__all__ = [
    "MESES_JANELA",
    "PARSER_VERSION",
    "BdrClient",
    "BdrDividendProvider",
    "PdfCache",
    "conteudo_e_pdf",
    "decodificar_pdf",
    "extrair_texto",
    "filtrar_avisos",
    "id_protocolo",
    "itens_de_noticias",
    "janelas_mensais",
    "listar_avisos",
    "parse_dividendo",
    "raiz_ticker",
    "resolver_url_documento",
]
