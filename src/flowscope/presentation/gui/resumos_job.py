"""Trabalho em background do resumo em lote dos documentos pendentes.

A função de trabalho prepara o texto (reutilizando o cache) e gera os resumos,
publicando progresso, resultado por documento e erro no :class:`JobContext`;
a thread do Tk aplica os resultados pelo gerenciador, respeitando a
thread-safety. Resultados não definitivos (parcial, falha ou protegido) são
pulados e permanecem pendentes para nova tentativa. Qualquer erro por documento
interrompe o lote, salvo quando ``continuar_em_erro``.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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
from flowscope.application.finalizacao_extracao import ItemPendente
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.llm import LLMRateLimitError
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

__all__ = [
    "FASE_PREPARAR",
    "FASE_RESUMIR",
    "GRUPO",
    "POLITICA",
    "ItemPendente",
    "MotivoExtracao",
    "ResultadoResumos",
    "executar_resumos",
]


class MotivoExtracao(Enum):
    """Motivo da classificação de uma extração do lote."""

    OK = "ok"
    PARCIAL = "parcial"
    FALHA = "falha"
    PROTEGIDO = "protegido"
    SEM_TEXTO = "sem_texto"
    APONTADOR = "apontador"


@dataclass
class ResultadoResumos:
    """Desfecho do lote com os conjuntos de itens por motivo de extração.

    ``sem_texto`` preserva a contagem de itens não resumíveis exibida no
    desfecho padrão; os demais campos classificam os itens de extração não
    conclusiva (parciais, falhas e protegidos) que alimentam a confirmação de
    finalização, além dos apontadores de notícia não resolvidos (excluídos).
    """

    sem_texto: int = 0
    parciais: list[ItemPendente] = field(default_factory=list)
    falhas: list[ItemPendente] = field(default_factory=list)
    protegidos: list[ItemPendente] = field(default_factory=list)
    apontadores: list[DocumentoArquivo] = field(default_factory=list)

    @property
    def nao_conclusivos(self: "ResultadoResumos") -> list[ItemPendente]:
        """Itens de extração não conclusiva, na ordem de processamento."""
        return [*self.parciais, *self.falhas, *self.protegidos]

#: Grupo de exclusão e política do resumo em lote.
GRUPO = "resumos"
POLITICA = Politica.LATEST_WINS

#: Rótulos das duas fases do lote.
FASE_PREPARAR = "⏳ Preparando textos"
FASE_RESUMIR = "⏳ Resumindo documentos"

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
    senhas: dict[Path, str] | None = None,
) -> ResultadoResumos:
    """Prepara textos e gera resumos, devolvendo o desfecho classificado.

    Quando ``continuar_em_erro`` é verdadeiro, uma falha por item é publicada e
    o lote prossegue com os demais; caso contrário, o lote é interrompido no
    primeiro erro. ``senhas`` associa caminho à senha pré-coletada de itens
    protegidos, mantendo o worker não-interativo.

    A classificação é acumulada durante a preparação: se o lote for cancelado
    ou abortado por timeout, o desfecho parcial já processado é devolvido para
    que a interface ofereça reprocessar/finalizar apenas esses itens.
    """
    resultado = ResultadoResumos()
    try:
        preparacao = _preparar_textos(
            ctx, painel, arquivos, continuar_em_erro, senhas, resultado
        )
        if preparacao is None:
            return resultado
        _resumir(ctx, painel, preparacao, continuar_em_erro)
    except OperacaoCancelada:
        logger.debug("Resumo em lote interrompido pelo usuário")
    return resultado


def _preparar_textos(
    ctx: JobContext,
    painel: _PainelDocumentos,
    arquivos: list[DocumentoArquivo],
    continuar_em_erro: bool,
    senhas: dict[Path, str] | None = None,
    resultado: ResultadoResumos | None = None,
) -> list[tuple[DocumentoArquivo, str]] | None:
    """Prepara os textos e classifica cada item pelo motivo da extração.

    Acumula a classificação em ``resultado`` (criado quando ausente), de modo
    que itens já processados sobrevivam a uma interrupção. Retorna os itens com
    texto, ou ``None`` quando um erro interrompe a fase.
    """
    total = len(arquivos)
    _progresso(ctx, 1, 0, total)
    mapa = senhas or {}
    if resultado is None:
        resultado = ResultadoResumos()
    com_texto: list[tuple[DocumentoArquivo, str]] = []
    for indice, arquivo in enumerate(arquivos, start=1):
        ctx.raise_if_cancelled()
        try:
            extracao = painel.preparar_texto(arquivo, mapa.get(arquivo.caminho))
        except Exception as exc:
            ctx.erro(exc, dados=arquivo)
            if not continuar_em_erro:
                return None
            continue
        _acumular(painel, arquivo, extracao, com_texto, resultado)
        _progresso(ctx, 1, indice, total)
    resultado.sem_texto = total - len(com_texto)
    return com_texto


def _acumular(
    painel: _PainelDocumentos,
    arquivo: DocumentoArquivo,
    extracao: ExtracaoTexto,
    com_texto: list[tuple[DocumentoArquivo, str]],
    resultado: ResultadoResumos,
) -> None:
    """Classifica a extração e a acumula no desfecho do lote."""
    motivo = _motivo(painel, arquivo, extracao)
    if motivo is MotivoExtracao.OK:
        com_texto.append((arquivo, extracao.texto))
        return
    if motivo is MotivoExtracao.APONTADOR:
        resultado.apontadores.append(arquivo)
        return
    if motivo is MotivoExtracao.SEM_TEXTO:
        return
    item = ItemPendente(
        arquivo, extracao.status, extracao.texto, extracao.paginas_com_falha
    )
    if motivo is MotivoExtracao.PARCIAL:
        resultado.parciais.append(item)
    elif motivo is MotivoExtracao.FALHA:
        resultado.falhas.append(item)
    else:
        resultado.protegidos.append(item)


def _motivo(
    painel: _PainelDocumentos,
    arquivo: DocumentoArquivo,
    resultado: ExtracaoTexto,
) -> MotivoExtracao:
    """Classifica a extração pelo motivo observável.

    Parcial, falha e protegido permanecem pendentes; ausência definitiva é
    excluída. Painéis que distinguem texto resolvido de conteúdo sem valor (por
    exemplo, notícias "Geral" cujo documento vinculado não foi baixado) expõem
    ``texto_utilizavel``; quando ele recusa um texto completo, o item é um
    apontador não resolvido. Na ausência do método, vale o texto extraível
    genérico.
    """
    if resultado.status is StatusExtracao.PARCIAL:
        return MotivoExtracao.PARCIAL
    if resultado.status is StatusExtracao.FALHA:
        return MotivoExtracao.FALHA
    if resultado.status is StatusExtracao.PROTEGIDO:
        return MotivoExtracao.PROTEGIDO
    if resultado.status is StatusExtracao.SEM_TEXTO:
        return MotivoExtracao.SEM_TEXTO
    if not tem_texto(resultado.texto):
        return MotivoExtracao.SEM_TEXTO
    metodo = getattr(painel, "texto_utilizavel", None)
    if metodo is not None and not metodo(arquivo, resultado.texto):
        return MotivoExtracao.APONTADOR
    return MotivoExtracao.OK


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
        except LLMRateLimitError as exc:
            # Cota/limite do provedor esgotado: interrompe o lote mesmo quando a
            # política é continuar em erro, pois insistir não tem chance de êxito.
            ctx.erro(exc, dados=arquivo)
            return
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
