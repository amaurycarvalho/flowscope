"""Extração de texto dos PDFs de avisos aos acionistas de BDR.

Os PDFs usam fontes embutidas com ``/ToUnicode``; a extração é delegada ao
``pypdf``. Uma falha de extração é tolerada e resulta em texto vazio, para que
o aviso seja ignorado sem interromper os demais.
"""

import logging
from io import BytesIO

logger = logging.getLogger("flowscope")


def extrair_texto(dados_pdf: bytes) -> str:
    """Extrai e concatena o texto de todas as páginas do PDF.

    Retorna string vazia quando o PDF não pode ser lido ou não contém texto
    extraível.
    """
    if not dados_pdf:
        return ""
    try:
        from pypdf import PdfReader
    except ImportError:  # dependência opcional ausente
        logger.warning("pypdf indisponível para extrair texto de BDR")
        return ""
    try:
        leitor = PdfReader(BytesIO(dados_pdf))
        return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except Exception:  # PDF corrompido ou encoding atípico
        logger.warning("Falha ao extrair texto do PDF de BDR", exc_info=True)
        return ""
