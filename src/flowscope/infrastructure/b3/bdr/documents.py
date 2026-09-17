"""Resolução e decodificação do PDF de um aviso aos acionistas de BDR.

A página ``Detail`` do Plantão B3 aponta para o documento no visualizador da
CVM; o PDF é obtido por POST ``ExibirPDF``, que devolve JSON com o conteúdo em
base64. O sistema valida que o conteúdo decodificado começa com ``%PDF``.
"""

import base64
import logging
import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("flowscope")

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


def decodificar_pdf(payload: object) -> bytes | None:
    """Decodifica o PDF de um payload ``{"d": "<base64>"}``.

    Retorna ``None`` quando o payload não contém o campo, quando o base64 é
    inválido ou quando o conteúdo não começa com ``%PDF``.
    """
    conteudo = payload.get("d") if isinstance(payload, dict) else None
    if not isinstance(conteudo, str) or not conteudo:
        return None
    try:
        dados = base64.b64decode(conteudo, validate=True)
    except ValueError:
        logger.warning("Conteúdo base64 inválido no aviso de BDR", exc_info=True)
        return None
    if not conteudo_e_pdf(dados):
        return None
    return dados


def conteudo_e_pdf(dados: bytes) -> bool:
    """Indica se o conteúdo começa com a assinatura ``%PDF``."""
    return dados.startswith(b"%PDF")
