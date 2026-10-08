"""Extração resiliente de texto dos documentos em cache.

O HTML é convertido localmente e o PDF é lido com ``pypdf``. A extração devolve
um resultado tipado (:class:`ExtracaoTexto`) que distingue texto completo,
parcial, ausência de texto, falha de leitura e documento protegido, para que os
consumidores decidam exibir, cachear ou reprocessar. É uma regra de aplicação
(extração/parsing), consumida pela apresentação e pelo contexto do chat.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup

from flowscope.domain.documents.texto import SEM_TEXTO, tem_texto

logger = logging.getLogger("flowscope")

__all__ = [
    "SELETOR_CONTEUDO_DETALHE",
    "SEM_TEXTO",
    "ExtracaoTexto",
    "StatusExtracao",
    "extrair_arquivo",
    "extrair_pdf",
    "tem_texto",
    "texto_de_html",
    "texto_de_pdf",
    "texto_preview",
]

#: Seletor do corpo do artigo nas páginas do Plantão B3 (notícias "Geral").
SELETOR_CONTEUDO_DETALHE = "#conteudoDetalhe"


class StatusExtracao(Enum):
    """Estado observável de uma extração de texto."""

    OK = "ok"
    PARCIAL = "parcial"
    SEM_TEXTO = "sem_texto"
    FALHA = "falha"
    PROTEGIDO = "protegido"


@dataclass(frozen=True)
class ExtracaoTexto:
    """Resultado da extração de texto de um documento."""

    texto: str
    status: StatusExtracao
    paginas_com_falha: int = 0


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


def extrair_pdf(dados: bytes, senha: str | None = None) -> ExtracaoTexto:
    """Extrai o texto de um PDF, tolerando falhas por página e proteção.

    Devolve um :class:`ExtracaoTexto` cujo estado é ``OK`` (completo),
    ``PARCIAL`` (alguma página falhou), ``SEM_TEXTO`` (leu, sem texto),
    ``FALHA`` (não foi possível ler) ou ``PROTEGIDO`` (criptografado sem senha
    válida). Nunca propaga exceção da biblioteca de PDF.
    """
    if not dados:
        return ExtracaoTexto("", StatusExtracao.SEM_TEXTO)
    try:
        from pypdf import PdfReader
    except ImportError:  # dependência opcional ausente
        logger.warning("pypdf indisponível para extrair texto de PDF")
        return ExtracaoTexto("", StatusExtracao.FALHA)
    try:
        leitor = PdfReader(BytesIO(dados))
    except Exception:  # PDF corrompido ou encoding atípico
        logger.warning("Falha ao abrir o PDF", exc_info=True)
        return ExtracaoTexto("", StatusExtracao.FALHA)

    if getattr(leitor, "is_encrypted", False):
        try:
            resultado = leitor.decrypt(senha if senha is not None else "")
        except Exception:  # backend de criptografia ausente ou senha inválida
            logger.warning("Falha ao descriptografar o PDF", exc_info=True)
            return ExtracaoTexto("", StatusExtracao.PROTEGIDO)
        if not resultado:
            return ExtracaoTexto("", StatusExtracao.PROTEGIDO)

    try:
        paginas = list(leitor.pages)
    except Exception:  # árvore de páginas ilegível
        logger.warning("Falha ao ler as páginas do PDF", exc_info=True)
        return ExtracaoTexto("", StatusExtracao.FALHA)

    textos: list[str] = []
    falhas = 0
    for pagina in paginas:
        try:
            textos.append(pagina.extract_text() or "")
        except Exception:  # página isolada ilegível
            falhas += 1
    conteudo = "\n".join(texto for texto in textos if texto)
    if not conteudo.strip():
        if paginas and falhas == len(paginas):
            return ExtracaoTexto("", StatusExtracao.FALHA, falhas)
        return ExtracaoTexto("", StatusExtracao.SEM_TEXTO, falhas)
    status = StatusExtracao.PARCIAL if falhas else StatusExtracao.OK
    return ExtracaoTexto(conteudo, status, falhas)


def texto_de_pdf(dados: bytes) -> str:
    """Adaptador de compatibilidade: devolve somente o texto extraído do PDF."""
    return extrair_pdf(dados).texto


def extrair_arquivo(
    caminho: Path,
    seletor: str | None = None,
    senha: str | None = None,
) -> ExtracaoTexto:
    """Deriva o texto de um arquivo conforme o tipo, com estado tipado.

    ``seletor``, quando informado para HTML, restringe a extração a um elemento
    (notícias "Geral" usam o corpo do artigo do Plantão B3). ``senha`` é usada
    apenas na extração de PDF.
    """
    try:
        sufixo = caminho.suffix.lower()
        if sufixo in (".html", ".htm"):
            conteudo = texto_de_html(
                caminho.read_text(encoding="utf-8", errors="replace"), seletor
            )
            status = (
                StatusExtracao.OK if conteudo.strip() else StatusExtracao.SEM_TEXTO
            )
            return ExtracaoTexto(conteudo, status)
        if sufixo == ".pdf":
            return extrair_pdf(caminho.read_bytes(), senha)
    except OSError:
        logger.warning("Falha ao ler documento %s", caminho, exc_info=True)
        return ExtracaoTexto("", StatusExtracao.FALHA)
    return ExtracaoTexto("", StatusExtracao.SEM_TEXTO)


def texto_preview(caminho: Path, seletor: str | None = None) -> str:
    """Adaptador de compatibilidade: devolve somente o texto do arquivo.

    ``seletor``, quando informado para HTML, restringe a extração a um elemento
    (notícias "Geral" usam o corpo do artigo do Plantão B3).
    """
    return extrair_arquivo(caminho, seletor).texto
