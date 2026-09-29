"""Testes headless do trabalho puro da análise fundamentalista."""

import logging
from datetime import date

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Progresso, Resultado
from flowscope.presentation.gui.background.job import (
    JobHandle,
    Politica,
)
from flowscope.presentation.gui.fundamental_job import executar_fundamental

REFERENCIA = date(2026, 9, 4)


class _Analise:
    def __init__(self, ticker):
        self.ticker = ticker


class _CasoFake:
    def __init__(self):
        self.force_refresh = None
        self.cancel_token = None

    def execute(self, tickers, reference_date, progress_callback=None,
                force_refresh=False, cancel_token=None):
        self.force_refresh = force_refresh
        self.cancel_token = cancel_token
        for ticker in tickers:
            if progress_callback is not None:
                progress_callback(f"Analisando {ticker}", False)
        return [_Analise(ticker) for ticker in tickers]


def _contexto():
    handle = JobHandle(
        id=1, grupo="fundamental", politica=Politica.LATEST_WINS
    )
    eventos = []
    return JobContext(handle, eventos.append), eventos


class TestExecutarFundamental:
    def test_publica_progresso_e_resultado(self):
        ctx, eventos = _contexto()

        executar_fundamental(
            ctx, _CasoFake(), ["HGBS11", "HGLG11"], REFERENCIA
        )

        progressos = [e for e in eventos if isinstance(e, Progresso)]
        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert [p.atual for p in progressos] == [1, 2]
        assert [p.total for p in progressos] == [2, 2]
        assert len(resultados) == 1
        assert set(resultados[0].valor.keys()) == {"HGBS11", "HGLG11"}

    def test_token_e_repassado_ao_caso_de_uso(self):
        ctx, _ = _contexto()
        caso = _CasoFake()

        executar_fundamental(ctx, caso, ["HGBS11"], REFERENCIA)

        assert caso.cancel_token is ctx.token

    def test_cancelamento_nao_publica_erro(self, caplog):
        class _CasoCancelado:
            def execute(self, *args, **kwargs):
                raise OperacaoCancelada()

        ctx, eventos = _contexto()
        ctx.token.request()
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            executar_fundamental(ctx, _CasoCancelado(), ["HGBS11"], REFERENCIA)

        assert not any(isinstance(e, Erro) for e in eventos)
        assert "Falha na análise fundamentalista" not in caplog.text

    def test_erro_publica_evento_de_erro(self):
        class _CasoComErro:
            def execute(self, *args, **kwargs):
                raise RuntimeError("boom")

        ctx, eventos = _contexto()
        executar_fundamental(ctx, _CasoComErro(), ["HGBS11"], REFERENCIA)

        erros = [e for e in eventos if isinstance(e, Erro)]
        assert len(erros) == 1
        assert isinstance(erros[0].excecao, RuntimeError)

    def test_falha_recuperavel_marca_resultado(self):
        class _CasoComFalha(_CasoFake):
            houve_falha_recuperavel = True

        ctx, eventos = _contexto()
        executar_fundamental(ctx, _CasoComFalha(), ["HGBS11"], REFERENCIA)

        resultado = [e for e in eventos if isinstance(e, Resultado)][0]
        assert resultado.falhou is True

    def test_encaminha_force_refresh(self):
        ctx, _ = _contexto()
        caso = _CasoFake()

        executar_fundamental(ctx, caso, ["HGBS11"], REFERENCIA, force_refresh=True)

        assert caso.force_refresh is True

    def test_token_limpo_apos_substituicao(self):
        handle = JobHandle(
            id=2, grupo="fundamental", politica=Politica.LATEST_WINS
        )
        token = CancellationToken()
        handle.token = token
        ctx = JobContext(handle, lambda evento: None)
        assert ctx.cancelled is False
