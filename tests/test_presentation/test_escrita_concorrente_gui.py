"""Testes da participação da GUI no lock global de escrita."""

import contextlib
from datetime import date
from pathlib import Path

from flowscope.application.documentos.aquisicao import ResultadoAquisicao
from flowscope.presentation import composicao
from flowscope.presentation.gui import documentos_job, noticias_job
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import JobHandle, Politica


class _Registro:
    def __init__(self, entra: list, sai: list) -> None:
        self._entra = entra
        self._sai = sai

    def __call__(self, esperar: float = 30.0):
        @contextlib.contextmanager
        def _cm():
            self._entra.append(True)
            try:
                yield
            finally:
                self._sai.append(True)

        return _cm()


def _contexto() -> JobContext:
    handle = JobHandle(id=1, grupo="g", politica=Politica.LATEST_WINS)
    return JobContext(handle=handle, publicar=lambda evento: None)


class _AquisicaoFake:
    def __init__(self, resultado: int = 1) -> None:
        self._resultado = resultado

    def adquirir(self, ticker, reference_date, progress=None, cancel_token=None):
        return ResultadoAquisicao(novos=self._resultado)


class _AquisicaoNoticiasFake:
    def __init__(self, resultado: int = 3) -> None:
        self._resultado = resultado

    def adquirir(self, reference_date, progress=None, cancel_token=None):
        return self._resultado


class TestEscritaConcorrenteGui:
    def test_bloqueio_de_escrita_adquire_e_libera(self, tmp_path, monkeypatch):
        from flowscope.infrastructure.action_lock import ActionLock

        monkeypatch.setattr(
            composicao, "ActionLock", lambda: ActionLock(tmp_path / "acao.lock")
        )
        with composicao.bloqueio_de_escrita(esperar=0.1):
            pass
        # Após liberar, outro processo/thread pode adquirir imediatamente.
        ActionLock(tmp_path / "acao.lock").adquirir(esperar=0.1).liberar()

    def test_documentos_adquire_lock_na_escrita(self, monkeypatch):
        entra: list = []
        sai: list = []
        monkeypatch.setattr(
            composicao, "bloqueio_de_escrita", _Registro(entra, sai)
        )
        resultado = documentos_job.executar_documentos(
            _contexto(), _AquisicaoFake(), "PETR4", date(2026, 10, 14)
        )
        assert resultado.adquiridos == 1
        assert entra and sai

    def test_noticias_adquire_lock_na_escrita(self, monkeypatch):
        entra: list = []
        sai: list = []
        monkeypatch.setattr(
            composicao, "bloqueio_de_escrita", _Registro(entra, sai)
        )
        adquiridos = noticias_job.executar_noticias(
            _contexto(), _AquisicaoNoticiasFake(3), date(2026, 10, 14)
        )
        assert adquiridos == 3
        assert entra and sai
