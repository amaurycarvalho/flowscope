"""Extração de texto dos documentos em cache para pré-visualização.

O HTML é convertido localmente e o PDF é lido com ``pypdf``. Uma falha de
leitura ou um arquivo sem texto extraível resultam em string vazia, para que
o painel exiba uma mensagem informativa sem erro.
"""

import logging
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger("flowscope")

#: Mensagem exibida quando o arquivo não tem texto extraível.
SEM_TEXTO = "Sem texto extraível para pré-visualização."

#: Seletor do corpo do artigo nas páginas do Plantão B3 (notícias "Geral").
SELETOR_CONTEUDO_DETALHE = "#conteudoDetalhe"


def tem_texto(texto: str | None) -> bool:
    """Indica se o texto contém conteúdo extraído (e não o marcador de ausência)."""
    if not texto:
        return False
    limpo = texto.strip()
    return bool(limpo) and limpo != SEM_TEXTO


def texto_de_html(html: str, seletor: str | None = None) -> str:
    """Extrai o texto visível de um documento HTML.

    Com ``seletor`` informado e presente no HTML, extrai apenas o texto desse
    elemento (por exemplo, o corpo do artigo); caso contrário, extrai o texto
    da página inteira.
    """
    if not html:
        return ""
    try:
        sopa = BeautifulSoup(html, "html.parser")
        if seletor:
            elemento = sopa.select_one(seletor)
            if elemento is not None:
                return elemento.get_text("\n", strip=True)
        return sopa.get_text("\n", strip=True)
    except Exception:  # HTML malformado
        logger.warning("Falha ao extrair texto do HTML", exc_info=True)
        return ""


def texto_de_pdf(dados: bytes) -> str:
    """Extrai e concatena o texto de todas as páginas de um PDF."""
    if not dados:
        return ""
    try:
        from pypdf import PdfReader
    except ImportError:  # dependência opcional ausente
        logger.warning("pypdf indisponível para pré-visualizar PDF")
        return ""
    try:
        leitor = PdfReader(BytesIO(dados))
        return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except Exception:  # PDF corrompido ou encoding atípico
        logger.warning("Falha ao extrair texto do PDF", exc_info=True)
        return ""


def texto_preview(caminho: Path, seletor: str | None = None) -> str:
    """Deriva o texto de pré-visualização conforme o tipo do arquivo.

    ``seletor``, quando informado para HTML, restringe a extração a um elemento
    (notícias "Geral" usam o corpo do artigo do Plantão B3).
    """
    try:
        if caminho.suffix.lower() in (".html", ".htm"):
            return texto_de_html(
                caminho.read_text(encoding="utf-8", errors="replace"), seletor
            )
        if caminho.suffix.lower() == ".pdf":
            return texto_de_pdf(caminho.read_bytes())
    except OSError:
        logger.warning("Falha ao ler documento %s", caminho, exc_info=True)
        return ""
    return ""
