"""Guardião de operações para impedir execuções concorrentes."""

from collections.abc import Iterator
from contextlib import contextmanager


class OperationGuard:
    """Controla a execução exclusiva de uma operação por vez."""

    def __init__(self: "OperationGuard") -> None:
        """Inicializa o guardião com a operação livre (não ocupada)."""
        self._busy = False

    @contextmanager
    def acquire(self: "OperationGuard") -> Iterator[bool]:
        """Libera o acesso exclusivo, retornando True se a operação foi adquirida."""
        if self._busy:
            yield False
            return
        self._busy = True
        try:
            yield True
        finally:
            self._busy = False

    @property
    def is_busy(self: "OperationGuard") -> bool:
        """Indica se uma operação está em execução no momento."""
        return self._busy
