"""Trabalho em background do resumo em lote dos documentos pendentes.

A função de trabalho prepara o texto (reutilizando o cache) e gera os resumos,
publicando progresso, resultado por documento e erro no :class:`JobContext`;
a thread do Tk aplica os resultados pelo gerenciador, respeitando a
thread-safety. Resultados não definitivos (parcial, falha ou protegido) são
pulados e permanecem pendentes para nova tentativa. Qualquer erro por documento
interrompe o lote, salvo quando ``continuar_em_erro``.
"""

import logging
from typing import Protocol

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
    tem_texto,
)
from flowscope.application.documentos.lote import (
    PainelLote,
    gerar_resumo_do_lote,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

#: Grupo de exclusão e política do resumo em lote.
GRUPO = "resumos"
POLITICA = Politica.LATEST_WINS

#: Rótulos das duas fases do lote.
FASE_PREPARAR = "• Preparando textos"
FASE_RESUMIR = "• Resumindo documentos"

_ROTULOS = {1: FASE_PREPARAR, 2: FASE_RESUMIR}


class _PainelDocumentos(PainelLote, Protocol):
    """Fachada do painel de documentos usada pelo job de lote.

    Além do seam de persistência (``persistir_no_lote``/``gerar_e_persistir``/
    ``gerar_resumo_estrito``), expõe a preparação de texto e a avaliação de
    guidance.
    """

    def preparar_texto(
        self: "_PainelDocumentos", arquivo: DocumentoArquivo
    ) -> ExtracaoTexto:
        """Retorna o resultado da extração do documento, convertendo em *miss*."""
        ...

    def avaliar_guidance(
        self: "_PainelDocumentos",
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: ResumoDocumento | None = None,
    ) -> AvaliacaoGuidance | None:
        """Avalia o guidance do documento, devolvendo a avaliação ou ``None``."""
        ...


def executar_resumos(
    ctx: JobContext,
    painel: _PainelDocumentos,
    arquivos: list[DocumentoArquivo],
    continuar_em_erro: bool = False,
) -> int:
    """Prepara textos e gera resumos, retornando a contagem sem texto.

    Quando ``continuar_em_erro`` é verdadeiro, uma falha por item é publicada e
    o lote prossegue com os demais; caso contrário, o lote é interrompido no
    primeiro erro.
    """
    try:
        preparados = _preparar_textos(ctx, painel, arquivos, continuar_em_erro)
        if preparados is None:
            return 0
        _resumir(ctx, painel, preparados, continuar_em_erro)
    except OperacaoCancelada:
        logger.debug("Resumo em lote interrompido pelo usuário")
        return 0
    return len(arquivos) - len(preparados)


def _preparar_textos(
    ctx: JobContext,
    painel: _PainelDocumentos,
    arquivos: list[DocumentoArquivo],
    continuar_em_erro: bool,
) -> list[tuple[DocumentoArquivo, str]] | None:
    """Prepara os textos que faltam e retorna os que têm texto completo.

    Retorna ``None`` quando um erro interrompe a fase.
    """
    total = len(arquivos)
    _progresso(ctx, 1, 0, total)
    preparados: list[tuple[DocumentoArquivo, ExtracaoTexto]] = []
    for indice, arquivo in enumerate(arquivos, start=1):
        ctx.raise_if_cancelled()
        try:
            resultado = painel.preparar_texto(arquivo)
        except Exception as exc:
            ctx.erro(exc, dados=arquivo)
            if not continuar_em_erro:
                return None
            continue
        preparados.append((arquivo, resultado))
        _progresso(ctx, 1, indice, total)
    return [
        (arquivo, resultado.texto)
        for arquivo, resultado in preparados
        if _texto_utilizavel(painel, arquivo, resultado)
    ]


def _texto_utilizavel(
    painel: _PainelDocumentos,
    arquivo: DocumentoArquivo,
    resultado: ExtracaoTexto,
) -> bool:
    """Indica se o texto preparado serve para resumir.

    Apenas resultados completos são resumíveis; parcial, falha e protegido
    permanecem pendentes. Painéis que distinguem texto resolvido de conteúdo sem
    valor (por exemplo, notícias "Geral" cujo documento vinculado não foi
    baixado) expõem ``texto_utilizavel``; na ausência do método, vale o texto
    extraível genérico.
    """
    if resultado.status is not StatusExtracao.OK:
        return False
    metodo = getattr(painel, "texto_utilizavel", None)
    if metodo is not None:
        return bool(metodo(arquivo, resultado.texto))
    return tem_texto(resultado.texto)


def _avaliar_guidance(
    painel: _PainelDocumentos,
    arquivo: DocumentoArquivo,
    texto: str,
    resumo: ResumoDocumento | None,
) -> AvaliacaoGuidance | None:
    """Avalia o guidance devolvendo o resultado, sem interromper o lote."""
    try:
        return painel.avaliar_guidance(arquivo, texto, resumo)
    except Exception:  # falha isolada não deve abortar o lote
        logger.warning(
            "Falha ao avaliar guidance de %s", arquivo.caminho, exc_info=True
        )
        return None


def _resumir(
    ctx: JobContext,
    painel: _PainelDocumentos,
    com_texto: list[tuple[DocumentoArquivo, str]],
    continuar_em_erro: bool,
) -> None:
    """Gera e publica o resumo de cada documento com texto extraível."""
    total = len(com_texto)
    _progresso(ctx, 2, 0, total)
    for indice, (arquivo, texto) in enumerate(com_texto, start=1):
        ctx.raise_if_cancelled()
        try:
            resumo = gerar_resumo_do_lote(painel, arquivo, texto)
        except Exception as exc:
            ctx.erro(exc, dados=arquivo)
            if not continuar_em_erro:
                return
            continue
        avaliacao = _avaliar_guidance(painel, arquivo, texto, resumo)
        ctx.resultado(valor=(resumo, avaliacao), dados=arquivo)
        _progresso(ctx, 2, indice, total)


def _progresso(ctx: JobContext, fase: int, current: int, total: int) -> None:
    """Publica um progresso da fase corrente com o rótulo correspondente."""
    ctx.progress(
        detalhe=_ROTULOS[fase], atual=current, total=total, dados=fase
    )
