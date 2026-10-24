"""Trabalho em background da aquisição de documentos.

A função de trabalho executa a aquisição e, em seguida, o housekeeping de
deduplicação por conteúdo, publicando progresso e o término; a thread do Tk
remonta a árvore pelo gerenciador, respeitando a thread-safety.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from flowscope.application.cancellation import CancellationToken, OperacaoCancelada
from flowscope.application.documentos.aquisicao import ResultadoAquisicao
from flowscope.application.renda_fixa import ResultadoAquisicaoTitulos
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

#: Grupo de exclusão e política do trabalho de documentos.
GRUPO = "documentos"
POLITICA = Politica.LATEST_WINS


def executar_documentos(
    ctx: JobContext,
    aquisicao: object,
    ticker: str,
    reference_date: date,
    deduplicar: Callable[[str, object], None] | None = None,
) -> ResultadoAquisicao:
    """Executa a aquisição e o housekeeping, publicando progresso e término.

    Retorna o desfecho da aquisição (vazio em cancelamento ou falha).
    """

    def _progresso(current: int, total: int, label: str) -> None:
        ctx.progress(detalhe=label, atual=current, total=total)

    resultado = ResultadoAquisicao()
    from flowscope.presentation.composicao import bloqueio_de_escrita

    try:
        with bloqueio_de_escrita():
            resultado = (
                aquisicao.adquirir(
                    ticker,
                    reference_date,
                    progress=_progresso,
                    cancel_token=ctx.token,
                )
                or ResultadoAquisicao()
            )
    except OperacaoCancelada:
        logger.debug(
            "Aquisição de documentos de %s interrompida pelo usuário", ticker
        )
    except Exception:  # falha inesperada não deve travar a interface
        logger.warning(
            "Falha na aquisição de documentos de %s", ticker, exc_info=True
        )
    if deduplicar is None:
        return resultado
    try:
        with bloqueio_de_escrita():
            deduplicar(ticker, ctx.token)
    except OperacaoCancelada:
        logger.debug("Housekeeping de documentos interrompido pelo usuário")
    except Exception:  # housekeeping não deve travar a interface
        logger.warning(
            "Falha no housekeeping de documentos de %s", ticker, exc_info=True
        )
    return resultado


@dataclass(frozen=True)
class ResultadoAtualizacao:
    """Desfecho combinado das etapas de documentos e de títulos."""

    documentos: ResultadoAquisicao = field(default_factory=ResultadoAquisicao)
    titulos: ResultadoAquisicaoTitulos = field(
        default_factory=ResultadoAquisicaoTitulos
    )

    @property
    def falhas(self: "ResultadoAtualizacao") -> int:
        """Total de falhas isoladas das duas etapas."""
        return self.documentos.falhas + self.titulos.falhas

    @property
    def adquiridos(self: "ResultadoAtualizacao") -> int:
        """Total de itens novos ou reutilizados das duas etapas."""
        return self.documentos.adquiridos + self.titulos.adquiridos


class _ContextoEtapa:
    """Encapsula o contexto do job prefixando o rótulo de progresso da etapa."""

    def __init__(self: "_ContextoEtapa", ctx: JobContext, rotulo: str) -> None:
        """Guarda o contexto original e o rótulo da etapa."""
        self._ctx = ctx
        self._rotulo = rotulo

    @property
    def token(self: "_ContextoEtapa") -> CancellationToken:
        """Retorna o token de cancelamento do job."""
        return self._ctx.token

    def progress(
        self: "_ContextoEtapa",
        detalhe: str = "",
        atual: int | None = None,
        total: int | None = None,
        dados: object = None,
    ) -> None:
        """Publica o progresso prefixado com o nome da etapa."""
        self._ctx.progress(
            detalhe=f"{self._rotulo}: {detalhe}" if detalhe else self._rotulo,
            atual=atual,
            total=total,
            dados=dados,
        )

    def __getattr__(self: "_ContextoEtapa", nome: str) -> object:
        """Delega os demais atributos ao contexto original."""
        return getattr(self._ctx, nome)


def executar_titulos(
    ctx: JobContext,
    aquisicao: object,
    ticker: str,
    reference_date: date,
) -> ResultadoAquisicaoTitulos:
    """Executa a aquisição de títulos, publicando progresso e tolerando falhas."""
    from flowscope.presentation.composicao import bloqueio_de_escrita

    try:
        with bloqueio_de_escrita():
            return (
                aquisicao.adquirir(
                    ticker,
                    reference_date,
                    progress=lambda atual, total, rotulo: ctx.progress(
                        detalhe=rotulo, atual=atual, total=total
                    ),
                    cancel_token=ctx.token,
                )
                or ResultadoAquisicaoTitulos()
            )
    except OperacaoCancelada:
        logger.debug(
            "Aquisição de títulos de %s interrompida pelo usuário", ticker
        )
        return ResultadoAquisicaoTitulos()
    except Exception:  # falha inesperada não deve travar a interface
        logger.warning(
            "Falha na aquisição de títulos de %s", ticker, exc_info=True
        )
        return ResultadoAquisicaoTitulos(falhas=1)


def executar_atualizacao(
    ctx: JobContext,
    aquisicao_documentos: object,
    aquisicao_titulos: object,
    ticker: str,
    reference_date: date,
    deduplicar: Callable[[str, object], None] | None = None,
) -> ResultadoAtualizacao:
    """Executa documentos e títulos no mesmo job, preservando cada etapa."""
    documentos = executar_documentos(
        _ContextoEtapa(ctx, "Documentos"),
        aquisicao_documentos,
        ticker,
        reference_date,
        deduplicar,
    )
    titulos = executar_titulos(
        _ContextoEtapa(ctx, "Títulos"),
        aquisicao_titulos,
        ticker,
        reference_date,
    )
    return ResultadoAtualizacao(documentos=documentos, titulos=titulos)
