"""Resolução do documento de um aviso aos acionistas de BDR.

A página ``Detail`` do Plantão B3 aponta para o documento no visualizador da
CVM; o download e a validação do PDF ficam em ``infrastructure.cvm.pdf``.
"""

import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from flowscope.infrastructure.cvm.pdf import conteudo_e_pdf, decodificar_pdf

__all__ = [
    "conteudo_e_pdf",
    "decodificar_pdf",
    "id_protocolo",
    "resolver_url_documento",
]

#: Trecho que identifica o visualizador de arquivos externos da CVM.
_MARCADOR_DOCUMENTO = "frmExibirArquivoIPEExterno"

_URL_DOCUMENTO = re.compile(
    r"https?://[^\s\"'<>]*" + _MARCADOR_DOCUMENTO + r"[^\s\"'<>]*"
)


def resolver_url_documento(html: str) -> str | None:
    """Extrai a URL do documento da página ``Detail``, ou ``None`` sem link.

    A URL aparece no texto do ``<pre id="conteudoDetalhe">``; entidades HTML
    como ``&amp;`` são decodificadas pelo parser antes da busca.
    """
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for ancora in soup.find_all("a", href=True):
        href = str(ancora["href"])
        if _MARCADOR_DOCUMENTO in href:
            return href
    for atributo in ("data-url", "data-href", "onclick", "value"):
        for elemento in soup.find_all(attrs={atributo: True}):
            valor = str(elemento[atributo])
            encontrado = _URL_DOCUMENTO.search(valor)
            if encontrado is not None:
                return encontrado.group(0)
    encontrado = _URL_DOCUMENTO.search(soup.get_text(" "))
    if encontrado is not None:
        return encontrado.group(0)
    encontrado = _URL_DOCUMENTO.search(html)
    if encontrado is not None:
        return encontrado.group(0)
    return None


def id_protocolo(url_documento: str) -> str | None:
    """Extrai o ``ID`` do documento da URL do visualizador da CVM."""
    if not url_documento:
        return None
    consulta = parse_qs(urlparse(url_documento).query)
    for chave, valores in consulta.items():
        if chave.lower() == "id" and valores:
            return valores[0]
    return None
