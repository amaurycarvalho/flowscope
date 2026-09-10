"""Serialização de requisições por host (RFC-008 §25).

Garante no máximo uma requisição por vez para cada host, evitando consultas
concorrentes indiscriminadas às fontes externas.
"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse


class SerializadorPorHost:
    """Serializa o acesso concorrente por host usando um lock dedicado."""

    def __init__(self: "SerializadorPorHost") -> None:
        """Inicializa o serializador sem locks pré-criados."""
        self._locks: dict[str, threading.Lock] = {}
        self._guarda = threading.Lock()

    def _lock_do_host(self: "SerializadorPorHost", host: str) -> threading.Lock:
        """Retorna (criando se necessário) o lock de um host."""
        with self._guarda:
            return self._locks.setdefault(host, threading.Lock())

    @contextmanager
    def serializar(self: "SerializadorPorHost", url: str) -> Iterator[None]:
        """Adquire o lock do host da URL durante o bloco."""
        host = urlparse(url).netloc
        lock = self._lock_do_host(host)
        with lock:
            yield
