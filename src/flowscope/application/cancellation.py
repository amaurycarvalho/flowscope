"""Token de cancelamento cooperativo para operações longas.

As operações executadas em background (análise fundamentalista, aquisição de
documentos e resumo em lote) observam um token compartilhado no topo de seus
laços de trabalho. Ao detectar uma solicitação de cancelamento, o laço encerra
lançando :class:`OperacaoCancelada`, que não deve ser confundido com falha.
"""

import threading


class OperacaoCancelada(Exception):
    """Sinaliza que a operação foi interrompida por solicitação do usuário."""


class CancellationToken:
    """Token de cancelamento baseado em ``threading.Event``.

    Concentra a sinalização e a observação do cancelamento, permitindo que
    uma operação em background seja interrompida de forma cooperativa.
    """

    def __init__(self: "CancellationToken") -> None:
        """Inicializa o token sem solicitação de cancelamento pendente."""
        self._event = threading.Event()

    def request(self: "CancellationToken") -> None:
        """Sinaliza a solicitação de cancelamento."""
        self._event.set()

    def clear(self: "CancellationToken") -> None:
        """Remove uma solicitação de cancelamento anterior."""
        self._event.clear()

    @property
    def is_set(self: "CancellationToken") -> bool:
        """Indica se há uma solicitação de cancelamento pendente."""
        return self._event.is_set()

    def raise_if_cancelled(self: "CancellationToken") -> None:
        """Lança :class:`OperacaoCancelada` se o cancelamento foi solicitado."""
        if self._event.is_set():
            raise OperacaoCancelada()
