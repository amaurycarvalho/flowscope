"""Fixtures compartilhadas dos testes da camada de apresentação."""

import gc

import pytest


@pytest.fixture(autouse=True)
def _coletar_lixo_apos_teste():
    """Coleta objetos Tk não referenciados na thread principal.

    O Tk não é thread-safe: se ``tkinter.Variable``/``Image`` forem finalizados
    por uma thread de trabalho (como a de pré-visualização de documentos), o
    interpretador pode abortar. Coletar o lixo ao final de cada teste garante
    que esses finalizadores rodem na thread principal, antes que a próxima
    thread de trabalho seja disparada.
    """
    yield
    gc.collect()
