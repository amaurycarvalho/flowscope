"""Trabalho em background da finalização definitiva de extrações não conclusivas.

A finalização roda fora da thread do Tk, por item: persiste o texto definitivo
(parcial com nota; falha/protegido apenas a nota), gera e grava o resumo —
via LLM no parcial e determinístico na falha e no protegido — e avalia o
guidance quando há texto. A thread do Tk apenas orquestra e reflete pelo
gerenciador, respeitando a thread-safety.
"""

import logging
from typing import Protocol

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.finalizacao_extracao import (
    ItemPendente,
    resumo_deterministico,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.documents.texto import tem_texto
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.resumos_job import GRUPO, POLITICA

logger = logging.getLogger("flowscope")

__all__ = ["GRUPO", "POLITICA", "executar_finalizacao"]

#: Rótulo de progresso da finalização.
FASE_FINALIZAR = "⏳ Finalizando extração"


class _PainelFinalizacao(Protocol):
    """Contrato do painel usado pelo job de finalização."""

    def persistir_texto_definitivo(
        self: "_PainelFinalizacao",
        arquivo: DocumentoArquivo,
        status: StatusExtracao,
        texto: str,
        paginas_com_falha: int = 0,
    ) -> str:
        """Grava o texto definitivo e devolve o texto gravado."""
        ...

    def gerar_e_persistir(
        self: "_PainelFinalizacao", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera e grava o resumo via LLM."""
        ...

    def persistir_resumo_definitivo(
        self: "_PainelFinalizacao",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> None:
        """Grava um resumo já produzido (caminho determinístico)."""
        ...

    def avaliar_guidance(
        self: "_PainelFinalizacao",
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: ResumoDocumento | None = None,
    ) -> AvaliacaoGuidance | None:
        """Avalia o guidance do documento, devolvendo a avaliação ou ``None``."""
        ...


def executar_finalizacao(
    ctx: JobContext,
    painel: _PainelFinalizacao,
    itens: list[ItemPendente],
) -> None:
    """Finaliza cada item não conclusivo como definitivo."""
    total = len(itens)
    ctx.progress(detalhe=FASE_FINALIZAR, atual=0, total=total)
    for indice, item in enumerate(itens, start=1):
        ctx.raise_if_cancelled()
        ctx.descrever(f"{item.arquivo.ticker}/{item.arquivo.nome}")
        try:
            _finalizar_item(painel, item)
        except Exception as exc:  # falha isolada não aborta os demais
            ctx.erro(exc, dados=item.arquivo)
        ctx.progress(detalhe=FASE_FINALIZAR, atual=indice, total=total)


def _finalizar_item(
    painel: _PainelFinalizacao, item: ItemPendente
) -> None:
    """Grava o texto e o resumo de um item, avaliando guidance se houver texto."""
    definitivo = painel.persistir_texto_definitivo(
        item.arquivo, item.status, item.texto, item.paginas_com_falha
    )
    resumo = _gerar_resumo(painel, item, definitivo)
    if tem_texto(definitivo):
        painel.avaliar_guidance(item.arquivo, definitivo, resumo)


def _gerar_resumo(
    painel: _PainelFinalizacao, item: ItemPendente, definitivo: str
) -> ResumoDocumento | None:
    """Gera o resumo pelo caminho do status: LLM no parcial, fixo nos demais."""
    if item.status is StatusExtracao.PARCIAL:
        return painel.gerar_e_persistir(item.arquivo, definitivo)
    resumo = resumo_deterministico(item.status)
    painel.persistir_resumo_definitivo(item.arquivo, resumo)
    return resumo
