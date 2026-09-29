"""Contexto entregue ao worker para publicar eventos sem tocar em widgets.

O :class:`JobContext` é o único ponto de contato do trabalho com o sistema de
background. Ele expõe o token de cancelamento do job e os métodos de
publicação (progresso, resultado, erro e término), sem acesso a widgets nem a
estruturas exclusivas da thread do Tk.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from flowscope.application.cancellation import CancellationToken
from flowscope.presentation.gui.background.events import (
    Confirmacao,
    Erro,
    Evento,
    Progresso,
    Resultado,
)

if TYPE_CHECKING:
    from flowscope.presentation.gui.background.job import JobHandle


@dataclass
class JobContext:
    """Interface segura entregue ao worker para publicar eventos."""

    handle: "JobHandle"
    publicar: Callable[[Evento], None]

    @property
    def token(self: "JobContext") -> CancellationToken:
        """Retorna o token de cancelamento do job."""
        return self.handle.token

    @property
    def cancelled(self: "JobContext") -> bool:
        """Indica se o cancelamento do job foi solicitado."""
        return self.handle.token.is_set

    def raise_if_cancelled(self: "JobContext") -> None:
        """Lança ``OperacaoCancelada`` se o job foi cancelado."""
        self.handle.token.raise_if_cancelled()

    def progress(
        self: "JobContext",
        detalhe: str = "",
        atual: int | None = None,
        total: int | None = None,
        dados: object = None,
    ) -> None:
        """Publica um evento de progresso."""
        self.publicar(
            Progresso(detalhe=detalhe, atual=atual, total=total, dados=dados)
        )

    def emit(self: "JobContext", evento: Evento) -> None:
        """Publica um evento arbitrário."""
        self.publicar(evento)

    def resultado(
        self: "JobContext",
        valor: object = None,
        falhou: bool = False,
        dados: object = None,
    ) -> None:
        """Publica o resultado de um trabalho ou de um item."""
        self.publicar(Resultado(valor=valor, falhou=falhou, dados=dados))

    def erro(self: "JobContext", excecao: BaseException, dados: object = None) -> None:
        """Publica uma falha do trabalho ou de um item."""
        self.publicar(Erro(excecao=excecao, dados=dados))

    def confirmar(
        self: "JobContext",
        quantidade: int,
        nomes: list[str],
        timeout: float | None = None,
    ) -> bool:
        """Pede confirmação à interface e aguarda a resposta na thread de trabalho.

        Publica um :class:`Confirmacao`, que a interface atende na thread do Tk,
        e bloqueia o worker até a resposta, o cancelamento do job ou o timeout.
        """
        evento = threading.Event()
        caixa: dict = {}
        self.publicar(
            Confirmacao(
                quantidade=quantidade,
                nomes=list(nomes),
                evento=evento,
                caixa=caixa,
            )
        )
        limite = None if timeout is None else time.monotonic() + timeout
        while True:
            if evento.wait(0.05):
                return bool(caixa.get("ok", False))
            if self.cancelled:
                return False
            if limite is not None and time.monotonic() >= limite:
                return False
