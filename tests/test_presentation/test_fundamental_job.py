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
    def execute(self, tickers, reference_date, progress_callback=None):
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

    def test_resultado_atualizado_propaga_flag(self):
        controller, presenter = self._controller(generation=1)
        job = FundamentalJob(_CasoFake(), ["HGBS11"], REFERENCIA, 1)
        job.fila.put(("resultado", {"HGBS11": _Analise("HGBS11")}, True))
        controller._fundamental_job = job
        controller._drenar_fundamental(job)
        assert presenter.on_fundamental_result.call_args[0][1] is True
