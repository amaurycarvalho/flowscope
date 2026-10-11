"""Fixtures compartilhadas dos testes de infraestrutura."""

import pytest

from flowscope.infrastructure import http_retry


@pytest.fixture(autouse=True)
def _sem_espera_de_retry(monkeypatch):
    """Neutraliza o backoff real do motor de retry nos testes.

    Testes que verificam a espera injetam ``sleep``/``jitter`` explicitamente;
    os demais não devem pagar as esperas reais de ``1``/``3``/``10`` segundos.
    """
    monkeypatch.setattr(http_retry, "_sleep_padrao", lambda _segundos: None)
