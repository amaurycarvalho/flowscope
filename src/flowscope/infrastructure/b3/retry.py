"""Retry de requisições HTTP da B3 para erros transitórios (RFC-008 §24).

Erros permanentes, como HTTP 400 e 404, não são repetidos; erros de rede e
status 5xx são tentados novamente com espera crescente.
"""

import time
from collections.abc import Callable, Sequence
from typing import TypeVar

import requests

#: Intervalos de espera (em segundos) antes de cada tentativa.
RETRY_DELAYS: tuple[float, ...] = (0, 1, 3, 10)

#: Status HTTP considerados permanentes e que não devem ser repetidos.
ERROS_PERMANENTES = frozenset({400, 404})

T = TypeVar("T")


def executar_com_retry(
    fn: Callable[[], T],
    *,
    delays: Sequence[float] = RETRY_DELAYS,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Executa ``fn`` repetindo erros transitórios com espera crescente."""
    ultimo_erro: requests.RequestException | None = None
    for atraso in delays:
        if atraso:
            sleep(atraso)
        try:
            return fn()
        except requests.RequestException as exc:
            if _permanente(exc):
                raise
            ultimo_erro = exc
    if ultimo_erro is not None:
        raise ultimo_erro
    raise RuntimeError("executar_com_retry exige ao menos uma tentativa")


def _permanente(exc: requests.RequestException) -> bool:
    """Indica se o erro HTTP é permanente e não deve ser repetido."""
    resposta = getattr(exc, "response", None)
    status = getattr(resposta, "status_code", None)
    return status in ERROS_PERMANENTES
