from datetime import date
from unittest.mock import MagicMock

from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.fundamental_job import (
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    FundamentalJob,
)

REFERENCIA = date(2026, 9, 4)


class _Analise:
    def __init__(self, ticker):
        self.ticker = ticker


class _CasoFake:
    def __init__(self):
        self.force_refresh = None

    def execute(self, tickers, reference_date, progress_callback=None,
                force_refresh=False):
        self.force_refresh = force_refresh
        for ticker in tickers:
            if progress_callback is not None:
                progress_callback(f"Analisando {ticker}", False)
        return [_Analise(ticker) for ticker in tickers]


class TestFundamentalJob:
    def test_publica_progresso_e_resultado_na_fila(self):
        job = FundamentalJob(_CasoFake(), ["HGBS11", "HGLG11"], REFERENCIA, 1)
        thread = job.iniciar()
        thread.join(timeout=2)

        mensagens = []
        while not job.fila.empty():
            mensagens.append(job.fila.get_nowait())
        tipos = [mensagem[0] for mensagem in mensagens]
        assert MENSAGEM_PROGRESSO in tipos
        assert MENSAGEM_RESULTADO in tipos

        resultado = [m for m in mensagens if m[0] == MENSAGEM_RESULTADO][0]
        assert set(resultado[1].keys()) == {"HGBS11", "HGLG11"}

    def test_erro_publica_mensagem_de_erro(self):
        class _CasoComErro:
            def execute(self, *args, **kwargs):
                raise RuntimeError("boom")

        job = FundamentalJob(_CasoComErro(), ["HGBS11"], REFERENCIA, 1)
        thread = job.iniciar()
        thread.join(timeout=2)
        tipo = job.fila.get_nowait()[0]
        assert tipo == "erro"

    def test_progresso_carrega_current_e_total(self):
        job = FundamentalJob(_CasoFake(), ["HGBS11", "HGLG11"], REFERENCIA, 1)
        thread = job.iniciar()
        thread.join(timeout=2)

        mensagens = []
        while not job.fila.empty():
            mensagens.append(job.fila.get_nowait())
        progressos = [m for m in mensagens if m[0] == MENSAGEM_PROGRESSO]
        assert [m[3] for m in progressos] == [1, 2]
        assert [m[4] for m in progressos] == [2, 2]


class TestGenerationToken:
    def _controller(self, generation):
        presenter = MagicMock()
        controller = FlowScopeController(
            guard=MagicMock(),
            load_portfolio=MagicMock(),
            analyze=MagicMock(),
            presenter=presenter,
            logger=MagicMock(),
            fundamental_repo=object(),
        )
        controller._fundamental_generation = generation
        return controller, presenter

    def test_resultado_obsoleto_e_descartado(self):
        controller, presenter = self._controller(generation=2)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put(("resultado", {"HGBS11": _Analise("HGBS11")}))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_result.assert_not_called()

    def test_resultado_atual_e_aplicado(self):
        controller, presenter = self._controller(generation=3)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 3)
        job.fila.put(("resultado", {"HGBS11": _Analise("HGBS11")}))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_result.assert_called_once()

    def test_resultado_propaga_flag_de_falha(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put(("resultado", {"HGBS11": _Analise("HGBS11")}, True))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        assert presenter.on_fundamental_result.call_args[0][1] is True

    def test_progresso_repassa_current_e_total(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put((MENSAGEM_PROGRESSO, "Analisando HGBS11", False, 1, 3))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_progress.assert_called_once_with(
            "Analisando HGBS11", 1, 3
        )

    def test_progresso_formato_antigo_nao_quebra(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put((MENSAGEM_PROGRESSO, "Analisando HGBS11", False))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_progress.assert_called_once_with(
            "Analisando HGBS11"
        )

    def test_drenar_encerra_cursor_no_resultado(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put(("resultado", {"HGBS11": _Analise("HGBS11")}))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_finished.assert_called_once()

    def test_drenar_erro_notifica_presenter_e_encerra_cursor(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put(("erro", "boom"))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        presenter.on_fundamental_error.assert_called_once()
        presenter.on_fundamental_finished.assert_called_once()


class TestJobFalhaRecuperavel:
    def test_job_publica_falha_recuperavel(self):
        class _CasoComFalha(_CasoFake):
            houve_falha_recuperavel = True

        job = FundamentalJob(_CasoComFalha(), ["HGBS11"], REFERENCIA, 1)
        thread = job.iniciar()
        thread.join(timeout=2)
        mensagens = []
        while not job.fila.empty():
            mensagens.append(job.fila.get_nowait())
        resultado = [m for m in mensagens if m[0] == MENSAGEM_RESULTADO][0]
        assert resultado[2] is True


class TestForceRefreshJob:
    def test_job_encaminha_force_refresh(self):
        caso = _CasoFake()
        job = FundamentalJob(caso, ["HGBS11"], REFERENCIA, 1, force_refresh=True)
        thread = job.iniciar()
        thread.join(timeout=2)
        assert caso.force_refresh is True

    def test_job_default_sem_force(self):
        caso = _CasoFake()
        job = FundamentalJob(caso, ["HGBS11"], REFERENCIA, 1)
        thread = job.iniciar()
        thread.join(timeout=2)
        assert caso.force_refresh is False
