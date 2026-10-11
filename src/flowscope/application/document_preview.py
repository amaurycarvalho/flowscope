"""Extração resiliente de texto dos documentos em cache.

O HTML é convertido localmente e o PDF é lido com ``pypdf``. A extração devolve
um resultado tipado (:class:`ExtracaoTexto`) que distingue texto completo,
parcial, ausência de texto, falha de leitura e documento protegido, para que os
consumidores decidam exibir, cachear ou reprocessar. É uma regra de aplicação
(extração/parsing), consumida pela apresentação e pelo contexto do chat.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
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
    "abrir_pdf",
    "extrair_arquivo",
    "extrair_pdf",
    "iterar_paginas",
    "montar_resultado",
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
    leitor, erro = abrir_pdf(dados, senha)
    if erro is not None:
        return erro
    gerador = iterar_paginas(leitor)
    if gerador is None:
        return ExtracaoTexto("", StatusExtracao.FALHA)
    textos: list[str] = []
    falhas = 0
    for texto, falhou in gerador:
        if falhou:
            falhas += 1
        else:
            textos.append(texto)
    return montar_resultado(textos, falhas)


def abrir_pdf(
    dados: bytes, senha: str | None = None
) -> tuple[object | None, ExtracaoTexto | None]:
    """Abre (e descriptografa) um PDF, devolvendo o leitor ou o erro tipado.

    Em sucesso devolve ``(leitor, None)``; caso contrário ``(None,
    ExtracaoTexto)`` com estado ``SEM_TEXTO`` (dados vazios), ``FALHA`` (não
    abriu) ou ``PROTEGIDO`` (criptografado sem senha válida).
    """
    if not dados:
        return None, ExtracaoTexto("", StatusExtracao.SEM_TEXTO)
    leitor = _abrir_leitor(dados)
    if leitor is None:
        return None, ExtracaoTexto("", StatusExtracao.FALHA)
    if not _liberar(leitor, senha):
        return None, ExtracaoTexto("", StatusExtracao.PROTEGIDO)
    return leitor, None


def iterar_paginas(
    leitor: object,
) -> Iterator[tuple[str, bool]] | None:
    """Itera ``(texto, falhou)`` por página, ou ``None`` se a árvore falhar.

    Cada página é extraída de forma isolada: uma falha — inclusive
    ``LimitReachedError`` (subclasse de ``PyPdfError``), que a biblioteca deixa
    propagar da extração — conta como página com falha e NÃO descarta as
    demais.
    """
    try:
        paginas = list(leitor.pages)  # type: ignore[attr-defined]
    except Exception:  # árvore de páginas ilegível
        logger.warning("Falha ao ler as páginas do PDF", exc_info=True)
        return None

    def _gerar() -> Iterator[tuple[str, bool]]:
        for pagina in paginas:
            try:
                yield pagina.extract_text() or "", False
            except Exception:  # página isolada ilegível (inclui LimitReachedError)
                yield "", True

    return _gerar()


def montar_resultado(textos: list[str], falhas: int) -> ExtracaoTexto:
    """Deriva o status final a partir do texto lido e das páginas com falha."""
    conteudo = "\n".join(texto for texto in textos if texto)
    if conteudo.strip():
        status = StatusExtracao.PARCIAL if falhas else StatusExtracao.OK
        return ExtracaoTexto(conteudo, status, falhas)
    if falhas and not textos:
        return ExtracaoTexto("", StatusExtracao.FALHA, falhas)
    return ExtracaoTexto("", StatusExtracao.SEM_TEXTO, falhas)


def _abrir_leitor(dados: bytes) -> object | None:
    """Instancia o leitor do PDF, devolvendo ``None`` se a leitura falhar."""
    try:
        from pypdf import PdfReader
    except ImportError:  # dependência opcional ausente
        logger.warning("pypdf indisponível para extrair texto de PDF")
        return None
    try:
        return PdfReader(BytesIO(dados))
    except Exception:  # PDF corrompido ou encoding atípico
        logger.warning("Falha ao abrir o PDF", exc_info=True)
        return None


def _liberar(leitor: object, senha: str | None) -> bool:
    """Indica se o leitor pode ser lido, descriptografando-o quando protegido."""
    if not getattr(leitor, "is_encrypted", False):
        return True
    try:
        resultado = leitor.decrypt(senha if senha is not None else "")
    except Exception:  # backend de criptografia ausente ou senha inválida
        logger.warning("Falha ao descriptografar o PDF", exc_info=True)
        return False
    return bool(resultado)


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
