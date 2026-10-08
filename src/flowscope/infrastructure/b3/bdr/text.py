"""Extração de texto dos PDFs de avisos aos acionistas de BDR.

A extração é delegada ao extrator unificado da camada de aplicação, para que a
resiliência (tolerância por página, proteção por senha, estados de falha) seja
a mesma em todos os consumidores. Uma falha de extração é tolerada e resulta em
texto vazio, para que o aviso seja ignorado sem interromper os demais.
"""

import logging

from flowscope.application.document_preview import extrair_pdf

logger = logging.getLogger("flowscope")


def extrair_texto(dados_pdf: bytes) -> str:
    """Extrai e concatena o texto de todas as páginas do PDF.

    Retorna string vazia quando o PDF não pode ser lido ou não contém texto
    extraível.
    """
    return extrair_pdf(dados_pdf).texto
