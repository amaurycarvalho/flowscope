"""Orquestração do resumo em lote de documentos, na camada de aplicação.

Prepara os textos e gera os resumos publicando progresso, resultado por
documento e erro por um contexto mínimo de progresso/cancelamento. Os painéis
(da GUI e da CLI) são as fachadas finas sobre este núcleo, expondo a preparação
de texto, a persistência e a avaliação de guidance. Resultados não definitivos
(parcial, falha ou protegido) permanecem pendentes para nova tentativa.

O contexto é o :class:`~flowscope.presentation.gui.background.context.JobContext`
na GUI ou qualquer objeto que satisfaça :class:`ContextoLote`.
"""

from __future__ import annotations

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
from flowscope.application.documentos.lote import gerar_resumo_do_lote
from flowscope.application.finalizacao_extracao import ItemPendente
from flowscope.application.renda_fixa.resultados import ResultadoInferencia
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.llm import LLMRateLimitError

logger = logging.getLogger("flowscope")

#: Rótulos das fases do lote.
FASE_PREPARAR = "⏳ Preparando textos"
FASE_RESUMIR = "⏳ Resumindo documentos"
FASE_INFERIR = "inferência de direitos e obrigações"

_ROTULOS = {1: FASE_PREPARAR, 2: FASE_RESUMIR, 3: FASE_INFERIR}


class ContextoLote(Protocol):
    """Interface mínima de progresso e cancelamento usada pela orquestração."""

    def raise_if_cancelled(self: ContextoLote) -> None:
        """Interrompe o lote quando o cancelamento foi solicitado."""
        ...

    def descrever(self: ContextoLote, texto: str) -> None:
        """Descreve o item corrente."""
        ...

    def progress(
        self: ContextoLote,
        detalhe: str,
        atual: int,
        total: int,
        dados: object = None,
    ) -> None:
        """Publica o progresso da fase corrente."""
        ...

    def erro(self: ContextoLote, excecao: BaseException, dados: object = None) -> None:
        """Publica uma falha por item."""
        ...

    def resultado(self: ContextoLote, valor: object, dados: object = None) -> None:
        """Publica o resultado de um item."""
        ...


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
    inferencia: ResultadoInferencia = field(default_factory=ResultadoInferencia)

    @property
    def nao_conclusivos(self: ResultadoResumos) -> list[ItemPendente]:
        """Itens de extração não conclusiva, na ordem de processamento."""
        return [*self.parciais, *self.falhas, *self.protegidos]


class PainelDocumentos(Protocol):
    """Fachada do painel usada pela orquestração do lote."""

    def preparar_texto(
        self: PainelDocumentos, arquivo: DocumentoArquivo, senha: str | None = None
    ) -> ExtracaoTexto:
        """Retorna o resultado da extração do documento, convertendo em *miss*."""
        ...

    def persistir_no_lote(self: PainelDocumentos) -> bool:
        """Indica se o lote deve gravar o resumo na thread de trabalho."""
        ...

    def gerar_e_persistir(
        self: PainelDocumentos, arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo e o grava no store, sem tocar em widgets."""
        ...

    def gerar_resumo_estrito(
        self: PainelDocumentos, arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo propagando falhas, sem gravar."""
        ...

    def avaliar_guidance(
        self: PainelDocumentos,
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: ResumoDocumento | None = None,
    ) -> AvaliacaoGuidance | None:
        """Avalia o guidance do documento, devolvendo a avaliação ou ``None``."""
        ...


class InferenciaLote(Protocol):
    """Contrato mínimo da fase de inferência acoplada ao lote."""

    def executar(
        self: InferenciaLote,
        ticker: str,
        progress: object | None = None,
        cancelar: object | None = None,
    ) -> ResultadoInferencia:
        """Executa a inferência do ticker e devolve o desfecho próprio."""
        ...


def executar_resumos(
    ctx: ContextoLote,
    painel: PainelDocumentos,
    arquivos: list[DocumentoArquivo],
    continuar_em_erro: bool = False,
    senhas: dict[Path, str] | None = None,
    inferencia: InferenciaLote | None = None,
    ticker: str | None = None,
) -> ResultadoResumos:
    """Prepara textos, gera resumos e executa a inferência opcional.

    Quando ``continuar_em_erro`` é verdadeiro, uma falha por item é publicada e
    o lote prossegue com os demais; caso contrário, o lote é interrompido no
    primeiro erro. ``senhas`` associa caminho à senha pré-coletada de itens
    protegidos, mantendo o worker não-interativo. ``inferencia`` roda depois dos
    resumos, com desfecho e progresso próprios, sem alterar as contagens.
    """
    resultado = ResultadoResumos()
    try:
        preparacao = _preparar_textos(
            ctx, painel, arquivos, continuar_em_erro, senhas, resultado
        )
        if preparacao is None:
            return resultado
        _resumir(ctx, painel, preparacao, continuar_em_erro)
        _inferir(ctx, inferencia, ticker or _ticker_de(arquivos), resultado)
    except OperacaoCancelada:
        logger.debug("Resumo em lote interrompido pelo usuário")
    return resultado


def _preparar_textos(
    ctx: ContextoLote,
    painel: PainelDocumentos,
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
        ctx.descrever(f"{arquivo.ticker}/{arquivo.nome}")
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
    painel: PainelDocumentos,
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
    painel: PainelDocumentos,
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
    painel: PainelDocumentos,
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
    ctx: ContextoLote,
    painel: PainelDocumentos,
    com_texto: list[tuple[DocumentoArquivo, str]],
    continuar_em_erro: bool,
) -> None:
    """Gera e publica o resumo de cada documento com texto extraível."""
    total = len(com_texto)
    _progresso(ctx, 2, 0, total)
    for indice, (arquivo, texto) in enumerate(com_texto, start=1):
        ctx.raise_if_cancelled()
        ctx.descrever(f"{arquivo.ticker}/{arquivo.nome}")
        try:
            resumo = gerar_resumo_do_lote(painel, arquivo, texto)
        except LLMRateLimitError as exc:
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


def _ticker_de(arquivos: list[DocumentoArquivo]) -> str | None:
    """Deriva o ticker do primeiro arquivo do lote, quando houver."""
    return arquivos[0].ticker if arquivos else None


def _inferir(
    ctx: ContextoLote,
    inferencia: InferenciaLote | None,
    ticker: str | None,
    resultado: ResultadoResumos,
) -> None:
    """Executa a fase de inferência, preservando os resumos em qualquer falha."""
    if inferencia is None or not ticker:
        return

    def progresso(atual: int, total: int, detalhe: str = "") -> None:
        _progresso(ctx, 3, atual, total)

    try:
        resultado.inferencia = inferencia.executar(
            ticker,
            progress=progresso,
            cancelar=ctx.raise_if_cancelled,
        )
    except OperacaoCancelada:
        resultado.inferencia = ResultadoInferencia(
            executada=True, cancelada=True
        )
    except Exception:  # falha isolada não invalida os resumos gravados
        logger.warning(
            "Falha na inferência de direitos e obrigações de %s",
            ticker,
            exc_info=True,
        )
        resultado.inferencia = ResultadoInferencia(executada=True, falhas=1)


def _progresso(ctx: ContextoLote, fase: int, current: int, total: int) -> None:
    """Publica um progresso da fase corrente com o rótulo correspondente."""
    ctx.progress(
        detalhe=_ROTULOS[fase], atual=current, total=total, dados=fase
    )
